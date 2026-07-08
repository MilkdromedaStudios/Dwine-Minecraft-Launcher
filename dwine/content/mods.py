"""Mod manager: one-click install, update, and remove with dependency resolution.

Every installed file is recorded in the profile's ``dwine-mods.json`` so
updates and uninstalls are exact — no orphaned jars, no guesswork.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.events import bus
from ..core.http import download
from ..launcher.profiles import Profile
from . import modrinth

_QUILT_FALLBACK = {"quilt": "fabric"}  # Quilt loads Fabric mods


class ModManager:
    def __init__(self, profile: Profile):
        self.profile = profile
        self.profile.mods_dir.mkdir(parents=True, exist_ok=True)

    # -- lockfile ------------------------------------------------------

    @property
    def _lock_path(self) -> Path:
        return self.profile.game_dir / "dwine-mods.json"

    def _lock(self) -> dict[str, Any]:
        if self._lock_path.exists():
            try:
                return json.loads(self._lock_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {"mods": {}}

    def _save_lock(self, lock: dict[str, Any]) -> None:
        self._lock_path.write_text(json.dumps(lock, indent=2), encoding="utf-8")

    def installed(self) -> dict[str, Any]:
        return self._lock()["mods"]

    # -- operations ------------------------------------------------------

    def _loaders_to_try(self) -> list[str]:
        loader = self.profile.loader
        loaders = [loader]
        if loader in _QUILT_FALLBACK:
            loaders.append(_QUILT_FALLBACK[loader])
        return loaders

    def resolve(self, slug: str) -> modrinth.ProjectVersion | None:
        for loader in self._loaders_to_try():
            version = modrinth.best_version(
                slug, game_version=self.profile.version, loader=loader
            )
            if version:
                return version
        return None

    def install(
        self, slug: str, with_dependencies: bool = True, _seen: set[str] | None = None
    ) -> list[str]:
        """Install a mod (and required dependencies). Returns installed slugs."""
        seen = _seen if _seen is not None else set()
        if slug in seen:
            return []
        seen.add(slug)

        version = self.resolve(slug)
        if version is None:
            raise LookupError(
                f"{slug!r} has no build for Minecraft {self.profile.version} "
                f"({self.profile.loader})"
            )
        file = version.primary_file
        dest = self.profile.mods_dir / file.filename
        download(file.url, dest, sha512=file.sha512 or None, size=file.size or None)

        lock = self._lock()
        old = lock["mods"].get(slug)
        if old and old.get("file") != file.filename:
            (self.profile.mods_dir / old["file"]).unlink(missing_ok=True)
        lock["mods"][slug] = {
            "version_id": version.id,
            "version": version.version_number,
            "file": file.filename,
        }
        self._save_lock(lock)
        bus.emit(
            "mods.installed",
            {"slug": slug, "version": version.version_number, "file": file.filename},
        )

        installed = [slug]
        if with_dependencies:
            for dep in version.dependencies:
                if dep.get("dependency_type") != "required":
                    continue
                dep_slug = self._dependency_slug(dep)
                if dep_slug:
                    installed += self.install(dep_slug, _seen=seen)
        return installed

    @staticmethod
    def _dependency_slug(dep: dict[str, Any]) -> str | None:
        project_id = dep.get("project_id")
        if not project_id:
            version_id = dep.get("version_id")
            if not version_id:
                return None
            project_id = modrinth.get_version_by_id(version_id).project_id
        project = modrinth.get_project(project_id)
        return project.get("slug") if project else None

    def remove(self, slug: str) -> bool:
        lock = self._lock()
        entry = lock["mods"].pop(slug, None)
        if not entry:
            return False
        (self.profile.mods_dir / entry["file"]).unlink(missing_ok=True)
        self._save_lock(lock)
        return True

    def update_all(self) -> dict[str, str]:
        """Re-resolve every installed mod; returns {slug: new_version} for changes."""
        changed: dict[str, str] = {}
        for slug, entry in list(self.installed().items()):
            version = self.resolve(slug)
            if version and version.id != entry.get("version_id"):
                self.install(slug, with_dependencies=False)
                changed[slug] = version.version_number
        return changed

    def orphaned_jars(self) -> list[Path]:
        """Jars in mods/ that Dwine did not install (user-managed files)."""
        tracked = {entry["file"] for entry in self.installed().values()}
        return [
            jar
            for jar in self.profile.mods_dir.glob("*.jar")
            if jar.name not in tracked
        ]

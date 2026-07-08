"""Shader manager: one-click shader packs via Iris.

Installing any shader automatically ensures Iris + Sodium are present
(the legitimate, high-performance shader stack for Fabric/Quilt).
"""

from __future__ import annotations

from pathlib import Path

from ..core.http import download
from ..launcher.profiles import Profile
from . import modrinth
from .mods import ModManager


class ShaderManager:
    def __init__(self, profile: Profile):
        self.profile = profile
        self.profile.shaderpacks_dir.mkdir(parents=True, exist_ok=True)

    def search(self, query: str, limit: int = 20) -> list[modrinth.ProjectHit]:
        return modrinth.search(
            query,
            project_type="shader",
            game_version=self.profile.version,
            limit=limit,
        )

    def ensure_iris(self) -> None:
        if self.profile.loader in ("fabric", "quilt"):
            ModManager(self.profile).install("iris")

    def install(self, slug: str, ensure_loader_mod: bool = True) -> Path:
        version = modrinth.best_version(slug, game_version=self.profile.version)
        if version is None:
            raise LookupError(
                f"{slug!r} has no build for Minecraft {self.profile.version}"
            )
        if ensure_loader_mod:
            self.ensure_iris()
        file = version.primary_file
        dest = self.profile.shaderpacks_dir / file.filename
        return download(file.url, dest, sha512=file.sha512 or None)

    def list(self) -> list[Path]:
        return sorted(
            self.profile.shaderpacks_dir.glob("*.zip"), key=lambda p: p.name.lower()
        )

    def remove(self, name: str) -> bool:
        target = self.profile.shaderpacks_dir / name
        if target.exists():
            target.unlink()
            return True
        return False

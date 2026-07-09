"""Resource pack manager: one-click install from Modrinth + local pack tools."""

from __future__ import annotations

from pathlib import Path

from ..core.http import download
from ..launcher.profiles import Profile
from . import modrinth


class ResourcePackManager:
    def __init__(self, profile: Profile):
        self.profile = profile
        self.profile.resourcepacks_dir.mkdir(parents=True, exist_ok=True)

    def search(self, query: str, limit: int = 20) -> list[modrinth.ProjectHit]:
        return modrinth.search(
            query,
            project_type="resourcepack",
            game_version=self.profile.effective_version(),
            limit=limit,
        )

    def install(self, slug: str) -> Path:
        game_version = self.profile.effective_version()
        version = modrinth.best_version(slug, game_version=game_version)
        if version is None:
            raise LookupError(
                f"{slug!r} has no pack for Minecraft {game_version}"
            )
        file = version.primary_file
        dest = self.profile.resourcepacks_dir / file.filename
        return download(file.url, dest, sha512=file.sha512 or None)

    def add_local(self, source: Path) -> Path:
        source = Path(source)
        dest = self.profile.resourcepacks_dir / source.name
        dest.write_bytes(source.read_bytes())
        return dest

    def list(self) -> list[Path]:
        return sorted(
            [
                p
                for p in self.profile.resourcepacks_dir.iterdir()
                if p.suffix == ".zip" or p.is_dir()
            ],
            key=lambda p: p.name.lower(),
        )

    def remove(self, name: str) -> bool:
        target = self.profile.resourcepacks_dir / name
        if target.is_file():
            target.unlink()
            return True
        if target.is_dir():
            import shutil

            shutil.rmtree(target)
            return True
        return False

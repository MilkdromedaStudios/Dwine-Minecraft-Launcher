"""Profiles: named, isolated game setups (FPS mode, PvP mode, Skyblock mode...).

Each profile owns its own game directory (worlds, servers.dat, options.txt,
mods, resource packs, shaders) so switching setups is instant and clean.
"""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..core import paths

BUILTIN_PRESETS: dict[str, dict[str, Any]] = {
    "fps": {
        "display_name": "FPS Mode",
        "loader": "fabric",
        "content_preset": "performance",
        "description": "Maximum frames: Sodium, Lithium and friends, minimal HUD.",
    },
    "pvp": {
        "display_name": "PvP Mode",
        "loader": "fabric",
        "content_preset": "pvp",
        "description": "Crisp hits: keystrokes, CPS, ping, sprint toggle, low latency.",
    },
    "skyblock": {
        "display_name": "Skyblock Mode",
        "loader": "forge",
        "content_preset": "skyblock",
        "description": "Hypixel Skyblock QoL: maps, timers, trackers — all rule-compliant.",
    },
    "cinematic": {
        "display_name": "Cinematic Mode",
        "loader": "fabric",
        "content_preset": "shaders",
        "description": "Iris + shaders, replay-friendly, motion blur.",
    },
}


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    return slug or "profile"


@dataclass
class Profile:
    name: str
    version: str  # Minecraft version id, or "" = latest release
    loader: str = "vanilla"  # vanilla | fabric | quilt | forge
    loader_version: str = ""  # "" = latest stable
    icon: str = "grass_block"
    jvm_args: list[str] = field(default_factory=list)
    memory_mb: int = 0  # 0 = inherit global setting
    server: str = ""  # one-click join target ("" = main menu)
    content_preset: str = ""
    features: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    @property
    def slug(self) -> str:
        return _slugify(self.name)

    @property
    def game_dir(self) -> Path:
        return paths.instances_dir() / self.slug

    @property
    def mods_dir(self) -> Path:
        return self.game_dir / "mods"

    @property
    def resourcepacks_dir(self) -> Path:
        return self.game_dir / "resourcepacks"

    @property
    def shaderpacks_dir(self) -> Path:
        return self.game_dir / "shaderpacks"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Profile":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


class ProfileStore:
    def __init__(self, root: Path | None = None):
        self.root = root or paths.profiles_dir()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, slug: str) -> Path:
        return self.root / f"{slug}.json"

    def save(self, profile: Profile) -> None:
        self._path(profile.slug).write_text(
            json.dumps(profile.to_dict(), indent=2), encoding="utf-8"
        )

    def load(self, name_or_slug: str) -> Profile:
        path = self._path(_slugify(name_or_slug))
        if not path.exists():
            raise KeyError(f"no such profile: {name_or_slug}")
        return Profile.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def delete(self, name_or_slug: str, remove_data: bool = False) -> None:
        profile = self.load(name_or_slug)
        self._path(profile.slug).unlink(missing_ok=True)
        if remove_data and profile.game_dir.exists():
            shutil.rmtree(profile.game_dir)

    def list(self) -> list[Profile]:
        return sorted(
            (
                Profile.from_dict(json.loads(p.read_text(encoding="utf-8")))
                for p in self.root.glob("*.json")
            ),
            key=lambda pr: pr.name.lower(),
        )

    def exists(self, name_or_slug: str) -> bool:
        return self._path(_slugify(name_or_slug)).exists()

    def create_from_preset(self, preset: str, version: str, name: str = "") -> Profile:
        spec = BUILTIN_PRESETS[preset]
        profile = Profile(
            name=name or spec["display_name"],
            version=version,
            loader=spec["loader"],
            content_preset=spec["content_preset"],
            description=spec["description"],
        )
        self.save(profile)
        return profile

    # -- export / import ----------------------------------------------

    def export(self, name_or_slug: str, dest: Path) -> Path:
        """Bundle a profile definition + its configs into a shareable zip."""
        profile = self.load(name_or_slug)
        dest = Path(dest)
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("dwine-profile.json", json.dumps(profile.to_dict(), indent=2))
            for rel in ("options.txt", "config", "resourcepacks", "shaderpacks"):
                src = profile.game_dir / rel
                if src.is_file():
                    zf.write(src, f"game/{rel}")
                elif src.is_dir():
                    for file in src.rglob("*"):
                        if file.is_file():
                            zf.write(file, f"game/{file.relative_to(profile.game_dir)}")
        return dest

    def import_(self, archive: Path, rename: str = "") -> Profile:
        with zipfile.ZipFile(archive) as zf:
            profile = Profile.from_dict(
                json.loads(zf.read("dwine-profile.json").decode("utf-8"))
            )
            if rename:
                profile.name = rename
            self.save(profile)
            for member in zf.namelist():
                if member.startswith("game/") and not member.endswith("/"):
                    target = profile.game_dir / member[len("game/"):]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(zf.read(member))
        return profile

"""Launcher self-update: checks GitHub releases for a newer Dwine."""

from __future__ import annotations

from dataclasses import dataclass

from .. import __version__
from ..core.http import get_json

RELEASES_API = "https://api.github.com/repos/MilkdromedaStudios/Dwine/releases/latest"


@dataclass
class UpdateInfo:
    current: str
    latest: str
    url: str
    notes: str

    @property
    def available(self) -> bool:
        return _parse(self.latest) > _parse(self.current)


def _parse(version: str) -> tuple[int, ...]:
    version = version.lstrip("vV")
    parts: list[int] = []
    for chunk in version.split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def check() -> UpdateInfo:
    data = get_json(RELEASES_API)
    return UpdateInfo(
        current=__version__,
        latest=data.get("tag_name", __version__),
        url=data.get("html_url", ""),
        notes=data.get("body", ""),
    )

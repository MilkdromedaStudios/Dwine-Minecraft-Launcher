"""Launcher self-update: checks GitHub releases and upgrades Dwine."""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass

from .. import __version__
from ..core.http import get_json

RELEASES_API = "https://api.github.com/repos/MilkdromedaStudios/Dwine/releases/latest"
REPO_URL = "git+https://github.com/MilkdromedaStudios/Dwine"


@dataclass
class UpdateInfo:
    current: str
    latest: str
    url: str
    notes: str

    @property
    def available(self) -> bool:
        return _parse(self.latest) > _parse(self.current)

    @property
    def install_target(self) -> str:
        tag = self.latest.lstrip()
        return f"dwine[full] @ {REPO_URL}@{tag}" if tag else f"dwine[full] @ {REPO_URL}"


def _parse(version: str) -> tuple[int, ...]:
    version = version.lstrip("vV")
    parts: list[int] = []
    for chunk in version.split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def check() -> UpdateInfo:
    """Return release information from GitHub without installing anything."""
    data = get_json(RELEASES_API)
    return UpdateInfo(
        current=__version__,
        latest=data.get("tag_name", __version__),
        url=data.get("html_url", ""),
        notes=data.get("body", ""),
    )


def apply(info: UpdateInfo | None = None) -> bool:
    """Upgrade Dwine in the current Python environment with pip.

    Returns ``True`` when pip was run. If Dwine is already current, returns
    ``False`` so callers can report that no update was needed.
    """
    info = info or check()
    if not info.available:
        return False
    if shutil.which("git") is None:
        raise RuntimeError("git is required to install Dwine updates from GitHub")
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        info.install_target,
    ])
    return True

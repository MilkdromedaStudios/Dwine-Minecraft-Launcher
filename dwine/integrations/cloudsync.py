"""Settings sync: snapshot/restore Dwine's config across machines.

Sync is file-based by design: point ``sync.folder`` at any synced
directory (Dropbox, Drive, Syncthing, a USB stick) and Dwine keeps a
versioned snapshot there. No Dwine account, no server, no telemetry.
Auth tokens are deliberately excluded from snapshots.
"""

from __future__ import annotations

import json
import time
import zipfile
from pathlib import Path

from .. import __version__
from ..core import paths
from ..core.config import get_config

SNAPSHOT_PREFIX = "dwine-sync-"


def _sync_folder() -> Path:
    folder = get_config().get("sync.folder", "")
    if not folder:
        raise RuntimeError("Set sync.folder in settings to a synced directory first.")
    path = Path(folder).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _payload_files() -> list[tuple[Path, str]]:
    """(source, archive-name) pairs. Never includes accounts/tokens."""
    entries: list[tuple[Path, str]] = []
    if paths.config_file().exists():
        entries.append((paths.config_file(), "settings.json"))
    for profile in paths.profiles_dir().glob("*.json"):
        entries.append((profile, f"profiles/{profile.name}"))
    for theme in paths.themes_dir().glob("*.json"):
        entries.append((theme, f"themes/{theme.name}"))
    return entries


def push() -> Path:
    """Write a new snapshot into the sync folder."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = _sync_folder() / f"{SNAPSHOT_PREFIX}{stamp}.zip"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "manifest.json",
            json.dumps({"dwine": __version__, "created": stamp}),
        )
        for source, arcname in _payload_files():
            zf.write(source, arcname)
    # Keep the five most recent snapshots.
    snapshots = sorted(_sync_folder().glob(f"{SNAPSHOT_PREFIX}*.zip"))
    for old in snapshots[:-5]:
        old.unlink(missing_ok=True)
    return dest


def latest_snapshot() -> Path | None:
    snapshots = sorted(_sync_folder().glob(f"{SNAPSHOT_PREFIX}*.zip"))
    return snapshots[-1] if snapshots else None


def pull(snapshot: Path | None = None) -> bool:
    """Restore settings/profiles/themes from the newest (or given) snapshot."""
    snapshot = snapshot or latest_snapshot()
    if snapshot is None:
        return False
    with zipfile.ZipFile(snapshot) as zf:
        for member in zf.namelist():
            if member == "manifest.json" or member.endswith("/"):
                continue
            if member == "settings.json":
                target = paths.config_file()
            elif member.startswith("profiles/"):
                target = paths.profiles_dir() / Path(member).name
            elif member.startswith("themes/"):
                target = paths.themes_dir() / Path(member).name
            else:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(member))
    get_config().reload()
    return True

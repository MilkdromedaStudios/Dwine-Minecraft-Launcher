"""Cross-platform application paths.

Dwine keeps its own data directory and gives every profile an isolated
game directory so vanilla installations are never touched.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Dwine"


def data_dir() -> Path:
    """Root directory for all Dwine data (config, instances, caches)."""
    override = os.environ.get("DWINE_HOME")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / APP_NAME.lower()


def cache_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / APP_NAME / "cache"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / APP_NAME
    base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / APP_NAME.lower()


def config_file() -> Path:
    return data_dir() / "settings.json"


def accounts_file() -> Path:
    return data_dir() / "accounts.json"


def profiles_dir() -> Path:
    return data_dir() / "profiles"


def instances_dir() -> Path:
    """Per-profile isolated .minecraft directories."""
    return data_dir() / "instances"


def versions_dir() -> Path:
    """Shared store of installed Minecraft versions."""
    return data_dir() / "meta" / "versions"


def libraries_dir() -> Path:
    return data_dir() / "meta" / "libraries"


def assets_dir() -> Path:
    return data_dir() / "meta" / "assets"


def java_dir() -> Path:
    """Managed Java runtimes downloaded by Dwine."""
    return data_dir() / "meta" / "java"


def themes_dir() -> Path:
    return data_dir() / "themes"


def plugins_dir() -> Path:
    return data_dir() / "plugins"


def logs_dir() -> Path:
    return data_dir() / "logs"


def ensure_tree() -> None:
    """Create the full directory layout on first run."""
    for path in (
        data_dir(),
        cache_dir(),
        profiles_dir(),
        instances_dir(),
        versions_dir(),
        libraries_dir(),
        assets_dir(),
        java_dir(),
        themes_dir(),
        plugins_dir(),
        logs_dir(),
    ):
        path.mkdir(parents=True, exist_ok=True)

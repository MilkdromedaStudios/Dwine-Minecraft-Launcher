"""Install a small ``dwine`` command shim into the user's PATH."""

from __future__ import annotations

import os
import shutil
import stat
import sys
from pathlib import Path


def user_bin_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(base) / "Python" / "Scripts"
    return Path(os.environ.get("DWINE_BIN_DIR", Path.home() / ".local" / "bin"))


def _shim_text() -> str:
    if sys.platform == "win32":
        return f'@echo off\n"{sys.executable}" -m dwine %*\n'
    return f'#!/usr/bin/env sh\nexec "{sys.executable}" -m dwine "$@"\n'


def install_command() -> Path:
    """Create or replace the per-user ``dwine`` launcher script."""
    bin_dir = user_bin_dir()
    bin_dir.mkdir(parents=True, exist_ok=True)
    name = "dwine.cmd" if sys.platform == "win32" else "dwine"
    target = bin_dir / name
    target.write_text(_shim_text(), encoding="utf-8")
    if sys.platform != "win32":
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return target


def command_on_path() -> bool:
    return shutil.which("dwine") is not None


def path_hint(command_path: Path | None = None) -> str:
    """Return exact PATH variable instructions and the shim file location."""
    bin_dir = user_bin_dir()
    command_path = command_path or bin_dir / ("dwine.cmd" if sys.platform == "win32" else "dwine")
    if sys.platform == "win32":
        return "\n".join([
            f"Command file location: {command_path}",
            "Environment variable to edit: Path (User environment variable)",
            f"Value to add as a new Path entry: {bin_dir}",
            "Windows UI: Settings → System → About → Advanced system settings "
            "→ Environment Variables → User variables → Path → Edit → New",
            "After saving, close and reopen your terminal, then run: dwine --help",
        ])

    shell_files = [Path.home() / ".bashrc", Path.home() / ".zshrc", Path.home() / ".profile"]
    files = ", ".join(str(path) for path in shell_files)
    return "\n".join([
        f"Command file location: {command_path}",
        "Environment variable to edit: PATH",
        f"Value to add to the front of PATH: {bin_dir}",
        f"Add this exact line to your shell startup file ({files}):",
        f'export PATH="{bin_dir}:$PATH"',
        "After saving, restart your terminal or run: source ~/.profile",
    ])

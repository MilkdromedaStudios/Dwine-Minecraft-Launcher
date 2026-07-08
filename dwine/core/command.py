"""Install Dwine launchers for terminals and desktop app menus."""

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


def _pythonw() -> str:
    if sys.platform == "win32":
        candidate = Path(sys.executable).with_name("pythonw.exe")
        if candidate.exists():
            return str(candidate)
    return sys.executable


def install_app_launcher() -> list[Path]:
    """Create a clickable Dwine launcher for the current desktop environment."""
    created: list[Path] = []
    if sys.platform == "win32":
        desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
        start_menu = (
            Path(os.environ.get("APPDATA", str(Path.home())))
            / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        )
        script = f'Set shell = CreateObject("WScript.Shell")\n' \
                 f'shell.Run """{_pythonw()}"" -m dwine ui", 0, False\n'
        for folder in (desktop, start_menu):
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / "Dwine.vbs"
            target.write_text(script, encoding="utf-8")
            created.append(target)
        return created

    if sys.platform == "darwin":
        app_dir = Path.home() / "Applications" / "Dwine.app"
        macos_dir = app_dir / "Contents" / "MacOS"
        macos_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / "Contents" / "Info.plist").write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleName</key><string>Dwine</string>
<key>CFBundleDisplayName</key><string>Dwine</string>
<key>CFBundleIdentifier</key><string>com.milkdromeda.dwine</string>
<key>CFBundleExecutable</key><string>dwine</string>
<key>CFBundlePackageType</key><string>APPL</string>
</dict></plist>
""",
            encoding="utf-8",
        )
        launcher = macos_dir / "dwine"
        launcher.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" -m dwine ui\n',
            encoding="utf-8",
        )
        launcher.chmod(
            launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )
        return [app_dir]

    apps_dir = (
        Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        / "applications"
    )
    apps_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = apps_dir / "dwine.desktop"
    desktop_file.write_text(
        "\n".join([
            "[Desktop Entry]",
            "Type=Application",
            "Name=Dwine",
            "Comment=Open the Dwine Minecraft Launcher",
            f'Exec={sys.executable} -m dwine ui',
            "Terminal=false",
            "Categories=Game;",
            "StartupNotify=true",
            "",
        ]),
        encoding="utf-8",
    )
    desktop_file.chmod(
        desktop_file.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )
    created.append(desktop_file)

    desktop_dir = Path.home() / "Desktop"
    if desktop_dir.exists():
        desktop_copy = desktop_dir / "Dwine.desktop"
        desktop_copy.write_text(
            desktop_file.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        desktop_copy.chmod(
            desktop_copy.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )
        created.append(desktop_copy)
    return created


def path_hint(command_path: Path | None = None) -> str:
    """Return exact PATH variable instructions and the shim file location."""
    bin_dir = user_bin_dir()
    name = "dwine.cmd" if sys.platform == "win32" else "dwine"
    command_path = command_path or bin_dir / name
    if sys.platform == "win32":
        return "\n".join([
            f"Command file location: {command_path}",
            "Environment variable to edit: Path (User environment variable)",
            f"Value to add as a new Path entry: {bin_dir}",
            "Windows UI: Settings → System → About → Advanced system settings "
            "→ Environment Variables → User variables → Path → Edit → New",
            "After saving, close and reopen your terminal, then run: dwine --help",
        ])

    shell_files = [
        Path.home() / ".bashrc",
        Path.home() / ".zshrc",
        Path.home() / ".profile",
    ]
    files = ", ".join(str(path) for path in shell_files)
    return "\n".join([
        f"Command file location: {command_path}",
        "Environment variable to edit: PATH",
        f"Value to add to the front of PATH: {bin_dir}",
        f"Add this exact line to your shell startup file ({files}):",
        f'export PATH="{bin_dir}:$PATH"',
        "After saving, restart your terminal or run: source ~/.profile",
    ])

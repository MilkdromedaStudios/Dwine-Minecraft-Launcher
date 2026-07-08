"""Build the game command line and run the game process.

Supports both the modern ``arguments`` format (1.13+) and the legacy
``minecraftArguments`` string, quick-play server join, custom resolution,
and per-profile isolated game directories.
"""

from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path
from typing import Any

from .. import __app_name__, __version__
from ..core import paths
from ..core.config import get_config
from ..core.events import bus
from . import install, java as java_mod
from .rules import rules_allow, substitute


def _classpath(version_data: dict[str, Any]) -> str:
    entries: list[str] = []
    seen: set[str] = set()
    for lib in version_data.get("libraries", []):
        if not rules_allow(lib.get("rules")):
            continue
        if lib.get("natives") and not lib.get("downloads", {}).get("artifact"):
            continue  # natives-only entry
        path = install.library_path(lib)
        if path is None:
            continue
        key = str(path)
        if key not in seen and path.exists():
            seen.add(key)
            entries.append(key)
    jar_owner = version_data.get("jar", version_data["id"])
    entries.append(str(install.client_jar_path(jar_owner)))
    return os.pathsep.join(entries)


def _variables(
    version_data: dict[str, Any],
    game_dir: Path,
    account: dict[str, Any],
    natives: Path,
    server: str | None,
) -> dict[str, str]:
    cfg = get_config()
    return {
        "auth_player_name": account.get("name", "Player"),
        "auth_uuid": account.get("uuid", "0" * 32),
        "auth_access_token": account.get("access_token", "0"),
        "auth_xuid": account.get("xuid", "0"),
        "auth_session": account.get("access_token", "0"),
        "clientid": account.get("client_id", "dwine"),
        "user_type": account.get("user_type", "msa"),
        "user_properties": "{}",
        "version_name": version_data["id"],
        "version_type": f"{__app_name__} {__version__}",
        "game_directory": str(game_dir),
        "assets_root": str(paths.assets_dir()),
        "assets_index_name": version_data.get("assetIndex", {}).get(
            "id", version_data.get("assets", "legacy")
        ),
        "game_assets": str(
            paths.assets_dir()
            / "virtual"
            / version_data.get("assets", "legacy")
        ),
        "natives_directory": str(natives),
        "launcher_name": __app_name__,
        "launcher_version": __version__,
        "classpath": _classpath(version_data),
        "resolution_width": str(cfg.get("game.width", 1280)),
        "resolution_height": str(cfg.get("game.height", 720)),
        "quickPlayPath": "",
        "quickPlaySingleplayer": "",
        "quickPlayMultiplayer": server or "",
        "quickPlayRealms": "",
    }


def _feature_flags(server: str | None) -> dict[str, bool]:
    cfg = get_config()
    return {
        "has_custom_resolution": True,
        "is_demo_user": False,
        "is_quick_play_multiplayer": bool(server),
        "is_quick_play_singleplayer": False,
        "is_quick_play_realms": False,
        "has_quick_plays_support": False,
        "is_fullscreen": bool(cfg.get("game.fullscreen", False)),
    }


def _expand_args(
    entries: list[Any],
    variables: dict[str, str],
    features: dict[str, bool],
) -> list[str]:
    out: list[str] = []
    for entry in entries:
        if isinstance(entry, str):
            out.append(substitute(entry, variables))
            continue
        if not rules_allow(entry.get("rules"), features):
            continue
        value = entry.get("value", [])
        values = [value] if isinstance(value, str) else value
        out.extend(substitute(v, variables) for v in values)
    return [arg for arg in out if arg != ""]


def build_command(
    version_data: dict[str, Any],
    game_dir: Path,
    account: dict[str, Any],
    java_bin: str | None = None,
    server: str | None = None,
    extra_jvm_args: list[str] | None = None,
) -> list[str]:
    cfg = get_config()
    natives = install.natives_dir(version_data["id"])
    variables = _variables(version_data, game_dir, account, natives, server)
    features = _feature_flags(server)
    java_bin = java_bin or java_mod.ensure_java(
        version_data, cfg.get("game.java_path", "")
    )

    memory = int(cfg.get("game.memory_mb", 4096))
    cmd: list[str] = [java_bin, f"-Xmx{memory}M", f"-Xms{min(memory, 1024)}M"]
    cmd += cfg.get("game.jvm_args", []) or []
    cmd += extra_jvm_args or []

    arguments = version_data.get("arguments")
    if arguments:
        cmd += _expand_args(arguments.get("jvm", []), variables, features)
    else:  # legacy versions: hardcoded JVM boilerplate
        cmd += [
            f"-Djava.library.path={natives}",
            "-cp",
            variables["classpath"],
        ]

    logging_cfg = version_data.get("logging", {}).get("client", {})
    if logging_cfg.get("file"):
        log_path = paths.assets_dir() / "log_configs" / logging_cfg["file"]["id"]
        if log_path.exists():
            cmd.append(
                substitute(logging_cfg.get("argument", ""), {"path": str(log_path)})
            )

    cmd.append(version_data["mainClass"])

    if arguments:
        cmd += _expand_args(arguments.get("game", []), variables, features)
    else:
        legacy = version_data.get("minecraftArguments", "")
        cmd += [
            substitute(part, variables)
            for part in legacy.split(" ")
            if substitute(part, variables)
        ]
        if server:
            host, _, port = server.partition(":")
            cmd += ["--server", host, "--port", port or "25565"]

    return cmd


def run(
    version_data: dict[str, Any],
    game_dir: Path,
    account: dict[str, Any],
    server: str | None = None,
    profile_name: str = "default",
    extra_jvm_args: list[str] | None = None,
) -> subprocess.Popen:
    """Launch the game and stream its output onto the event bus."""
    game_dir.mkdir(parents=True, exist_ok=True)
    cmd = build_command(
        version_data, game_dir, account, server=server, extra_jvm_args=extra_jvm_args
    )
    redacted = [
        "<token>" if arg == account.get("access_token") and arg != "0" else arg
        for arg in cmd
    ]
    bus.emit("game.launching", {"profile": profile_name, "command": redacted})
    proc = subprocess.Popen(
        cmd,
        cwd=str(game_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    )
    bus.emit("game.started", {"profile": profile_name, "pid": proc.pid})

    def pump() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            bus.emit("game.log", {"profile": profile_name, "line": line.rstrip("\n")})
        code = proc.wait()
        bus.emit("game.exited", {"profile": profile_name, "code": code})

    threading.Thread(target=pump, name=f"dwine-game-{profile_name}", daemon=True).start()
    return proc

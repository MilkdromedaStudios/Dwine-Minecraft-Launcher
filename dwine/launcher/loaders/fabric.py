"""Fabric loader installer, driven by the official Fabric meta API."""

from __future__ import annotations

import json

from ...core.http import get_json
from ..install import version_json_path

META = "https://meta.fabricmc.net/v2"


def supported_game_versions() -> list[str]:
    return [v["version"] for v in get_json(f"{META}/versions/game")]


def loader_versions(mc_version: str) -> list[dict]:
    return get_json(f"{META}/versions/loader/{mc_version}")


def latest_loader(mc_version: str) -> str:
    versions = loader_versions(mc_version)
    if not versions:
        raise RuntimeError(f"Fabric does not support Minecraft {mc_version}")
    for entry in versions:
        if entry["loader"].get("stable", True):
            return entry["loader"]["version"]
    return versions[0]["loader"]["version"]


def install(mc_version: str, loader_version: str = "") -> str:
    loader_version = loader_version or latest_loader(mc_version)
    profile = get_json(
        f"{META}/versions/loader/{mc_version}/{loader_version}/profile/json"
    )
    version_id = profile["id"]
    path = version_json_path(version_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return version_id

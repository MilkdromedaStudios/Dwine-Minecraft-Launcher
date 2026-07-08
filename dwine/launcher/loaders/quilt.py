"""Quilt loader installer, driven by the official Quilt meta API."""

from __future__ import annotations

import json

from ...core.http import get_json
from ..install import version_json_path

META = "https://meta.quiltmc.org/v3"


def loader_versions(mc_version: str) -> list[dict]:
    return get_json(f"{META}/versions/loader/{mc_version}")


def latest_loader(mc_version: str) -> str:
    versions = loader_versions(mc_version)
    if not versions:
        raise RuntimeError(f"Quilt does not support Minecraft {mc_version}")
    for entry in versions:
        version = entry["loader"]["version"]
        if "beta" not in version and "pre" not in version:
            return version
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

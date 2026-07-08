"""Forge installer.

Forge ships a Java installer that patches jars and generates processors'
output, so Dwine downloads the official installer and runs it headlessly
against its own version store — the exact same artifacts the official
installer would produce.
"""

from __future__ import annotations

import json
import subprocess

from ...core import paths
from ...core.events import bus
from ...core.http import download, get_json
from .. import install as install_mod
from .. import java as java_mod

PROMOTIONS_URL = (
    "https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json"
)
MAVEN = "https://maven.minecraftforge.net/net/minecraftforge/forge"


def recommended_version(mc_version: str) -> str:
    promos = get_json(PROMOTIONS_URL)["promos"]
    forge = promos.get(f"{mc_version}-recommended") or promos.get(
        f"{mc_version}-latest"
    )
    if not forge:
        raise RuntimeError(f"Forge does not support Minecraft {mc_version}")
    return forge


def install(mc_version: str, forge_version: str = "") -> str:
    forge_version = forge_version or recommended_version(mc_version)
    full = f"{mc_version}-{forge_version}"
    version_id = f"{mc_version}-forge-{forge_version}"
    if install_mod.version_json_path(version_id).exists():
        return version_id

    # The installer needs a vanilla install + launcher_profiles.json to target.
    install_mod.install_version(mc_version)
    target = paths.data_dir() / "meta"
    profiles_json = target / "launcher_profiles.json"
    if not profiles_json.exists():
        profiles_json.write_text(json.dumps({"profiles": {}}), encoding="utf-8")

    installer = paths.cache_dir() / f"forge-{full}-installer.jar"
    download(f"{MAVEN}/{full}/forge-{full}-installer.jar", installer)

    vanilla = install_mod.load_version_json(mc_version)
    java_bin = java_mod.ensure_java(vanilla)
    bus.emit("install.step", {"version": version_id, "step": "forge-installer"})
    result = subprocess.run(
        [java_bin, "-jar", str(installer), "--installClient", str(target)],
        capture_output=True,
        text=True,
        timeout=1200,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Forge installer failed ({result.returncode}):\n{result.stdout[-2000:]}"
            f"\n{result.stderr[-2000:]}"
        )
    if not install_mod.version_json_path(version_id).exists():
        # Some Forge builds name the version differently; find what appeared.
        for candidate in paths.versions_dir().iterdir():
            if "forge" in candidate.name and mc_version in candidate.name:
                return candidate.name
        raise RuntimeError("Forge installer finished but no version was produced")
    return version_id

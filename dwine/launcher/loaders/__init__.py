"""Mod loader installers: Fabric, Quilt, Forge (plus plain Vanilla).

Every installer returns the id of a version JSON placed in Dwine's
version store, ready for :func:`dwine.launcher.install.install_version`.
"""

from __future__ import annotations

from . import fabric, forge, quilt

LOADERS = ("vanilla", "fabric", "quilt", "forge")


def ensure_loader(loader: str, mc_version: str, loader_version: str = "") -> str:
    """Install loader metadata and return the launchable version id."""
    loader = (loader or "vanilla").lower()
    if loader == "vanilla":
        return mc_version
    if loader == "fabric":
        return fabric.install(mc_version, loader_version)
    if loader == "quilt":
        return quilt.install(mc_version, loader_version)
    if loader == "forge":
        return forge.install(mc_version, loader_version)
    raise ValueError(f"unknown loader: {loader!r} (expected one of {LOADERS})")

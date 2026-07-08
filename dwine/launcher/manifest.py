"""Mojang version manifest access with local caching."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core import paths
from ..core.http import get_json

VERSION_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
_CACHE_TTL = 15 * 60  # seconds


@dataclass(frozen=True)
class VersionInfo:
    id: str
    type: str  # release | snapshot | old_beta | old_alpha
    url: str
    release_time: str
    sha1: str

    @property
    def is_release(self) -> bool:
        return self.type == "release"


def _cache_path() -> Path:
    return paths.cache_dir() / "version_manifest_v2.json"


def fetch_manifest(force: bool = False) -> dict[str, Any]:
    cache = _cache_path()
    if not force and cache.exists() and time.time() - cache.stat().st_mtime < _CACHE_TTL:
        try:
            return json.loads(cache.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    try:
        data = get_json(VERSION_MANIFEST_URL)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data), encoding="utf-8")
        return data
    except Exception:
        # Offline: fall back to any cached copy, however old.
        if cache.exists():
            return json.loads(cache.read_text(encoding="utf-8"))
        raise


def list_versions(
    releases: bool = True,
    snapshots: bool = False,
    old_versions: bool = False,
) -> list[VersionInfo]:
    manifest = fetch_manifest()
    wanted = set()
    if releases:
        wanted.add("release")
    if snapshots:
        wanted.add("snapshot")
    if old_versions:
        wanted.update({"old_beta", "old_alpha"})
    return [
        VersionInfo(
            id=v["id"],
            type=v["type"],
            url=v["url"],
            release_time=v.get("releaseTime", ""),
            sha1=v.get("sha1", ""),
        )
        for v in manifest["versions"]
        if v["type"] in wanted
    ]


def latest_release() -> str:
    return fetch_manifest()["latest"]["release"]


def latest_snapshot() -> str:
    return fetch_manifest()["latest"]["snapshot"]


def find_version(version_id: str) -> VersionInfo:
    manifest = fetch_manifest()
    for v in manifest["versions"]:
        if v["id"] == version_id:
            return VersionInfo(
                id=v["id"],
                type=v["type"],
                url=v["url"],
                release_time=v.get("releaseTime", ""),
                sha1=v.get("sha1", ""),
            )
    raise KeyError(f"unknown Minecraft version: {version_id}")

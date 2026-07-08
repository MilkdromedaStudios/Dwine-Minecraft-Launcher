"""Vanilla version installer.

Downloads and verifies everything a version needs: version JSON, client
jar, libraries, native libraries, asset index + objects, and the log4j
config. All artifacts are checksum-verified and shared between profiles.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from ..core import paths
from ..core.config import get_config
from ..core.events import bus
from ..core.http import download, download_many
from . import manifest
from .rules import current_os, rules_allow

RESOURCES_URL = "https://resources.download.minecraft.net"


def version_json_path(version_id: str) -> Path:
    return paths.versions_dir() / version_id / f"{version_id}.json"


def client_jar_path(version_id: str) -> Path:
    return paths.versions_dir() / version_id / f"{version_id}.jar"


def load_version_json(version_id: str) -> dict[str, Any]:
    """Load a version JSON, resolving the ``inheritsFrom`` chain (modded versions)."""
    path = version_json_path(version_id)
    if not path.exists():
        info = manifest.find_version(version_id)
        download(info.url, path, sha1=info.sha1 or None)
    data = json.loads(path.read_text(encoding="utf-8"))
    parent_id = data.get("inheritsFrom")
    if parent_id:
        parent = load_version_json(parent_id)
        data = merge_version_json(parent, data)
    return data


def merge_version_json(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    """Merge a loader version JSON over its vanilla parent, vanilla-launcher style."""
    merged = dict(parent)
    for key, value in child.items():
        if key == "libraries":
            merged["libraries"] = list(value) + list(parent.get("libraries", []))
        elif key == "arguments":
            base = dict(parent.get("arguments", {}))
            for kind in ("game", "jvm"):
                base[kind] = list(base.get(kind, [])) + list(value.get(kind, []))
            merged["arguments"] = base
        elif key == "inheritsFrom":
            continue
        else:
            merged[key] = value
    merged.setdefault("jar", parent.get("id"))
    return merged


def library_path(lib: dict[str, Any]) -> Path | None:
    artifact = lib.get("downloads", {}).get("artifact")
    if artifact and artifact.get("path"):
        return paths.libraries_dir() / artifact["path"]
    # Maven-style coordinate fallback (Fabric/Quilt/Forge library entries).
    name = lib.get("name")
    if not name:
        return None
    return paths.libraries_dir() / maven_to_path(name)


def maven_to_path(coordinate: str) -> str:
    """``group:artifact:version[:classifier][@ext]`` -> repository path."""
    ext = "jar"
    if "@" in coordinate:
        coordinate, ext = coordinate.rsplit("@", 1)
    parts = coordinate.split(":")
    group, artifact, version = parts[0], parts[1], parts[2]
    classifier = f"-{parts[3]}" if len(parts) > 3 else ""
    return (
        f"{group.replace('.', '/')}/{artifact}/{version}/"
        f"{artifact}-{version}{classifier}.{ext}"
    )


def _native_classifier(lib: dict[str, Any]) -> str | None:
    natives = lib.get("natives")
    if not natives:
        return None
    key = natives.get(current_os())
    if not key:
        return None
    import struct

    bits = "64" if struct.calcsize("P") * 8 == 64 else "32"
    return key.replace("${arch}", bits)


def collect_libraries(version_data: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    """Split allowed libraries into (classpath_jobs, natives_jobs) download specs."""
    classpath: list[dict] = []
    natives: list[dict] = []
    for lib in version_data.get("libraries", []):
        if not rules_allow(lib.get("rules")):
            continue
        downloads = lib.get("downloads", {})
        artifact = downloads.get("artifact")
        if artifact and artifact.get("url"):
            classpath.append(
                {
                    "url": artifact["url"],
                    "dest": paths.libraries_dir() / artifact["path"],
                    "sha1": artifact.get("sha1"),
                    "size": artifact.get("size"),
                }
            )
        elif lib.get("name") and (lib.get("url") or not downloads):
            # Loader-style library: maven coordinate + repository base URL.
            rel = maven_to_path(lib["name"])
            base = (lib.get("url") or "https://libraries.minecraft.net/").rstrip("/")
            classpath.append({"url": f"{base}/{rel}", "dest": paths.libraries_dir() / rel})
        classifier = _native_classifier(lib)
        if classifier:
            native_artifact = downloads.get("classifiers", {}).get(classifier)
            if native_artifact:
                natives.append(
                    {
                        "url": native_artifact["url"],
                        "dest": paths.libraries_dir() / native_artifact["path"],
                        "sha1": native_artifact.get("sha1"),
                        "size": native_artifact.get("size"),
                    }
                )
    return classpath, natives


def natives_dir(version_id: str) -> Path:
    return paths.versions_dir() / version_id / "natives"


def extract_natives(version_data: dict[str, Any], native_jobs: list[dict]) -> Path:
    target = natives_dir(version_data["id"])
    target.mkdir(parents=True, exist_ok=True)
    for job in native_jobs:
        jar = Path(job["dest"])
        if not jar.exists():
            continue
        with zipfile.ZipFile(jar) as zf:
            for member in zf.namelist():
                if member.startswith("META-INF/") or member.endswith("/"):
                    continue
                zf.extract(member, target)
    return target


def install_assets(version_data: dict[str, Any], workers: int = 8) -> str:
    index_info = version_data.get("assetIndex")
    if not index_info:
        return version_data.get("assets", "legacy")
    index_id = index_info["id"]
    index_path = paths.assets_dir() / "indexes" / f"{index_id}.json"
    download(index_info["url"], index_path, sha1=index_info.get("sha1"))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    objects = index.get("objects", {})
    jobs = []
    seen: set[str] = set()
    for obj in objects.values():
        h = obj["hash"]
        if h in seen:
            continue
        seen.add(h)
        jobs.append(
            {
                "url": f"{RESOURCES_URL}/{h[:2]}/{h}",
                "dest": paths.assets_dir() / "objects" / h[:2] / h,
                "sha1": h,
                "size": obj.get("size"),
            }
        )
    bus.emit("install.step", {"step": "assets", "detail": f"{len(jobs)} objects"})
    download_many(jobs, workers=workers)
    # Very old versions read assets from a real directory tree.
    if index.get("virtual") or index.get("map_to_resources"):
        virtual_root = paths.assets_dir() / "virtual" / index_id
        for name, obj in objects.items():
            h = obj["hash"]
            src = paths.assets_dir() / "objects" / h[:2] / h
            dst = virtual_root / name
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
    return index_id


def install_version(version_id: str, workers: int | None = None) -> dict[str, Any]:
    """Fully install a version (vanilla or modded). Returns merged version JSON."""
    workers = workers or int(get_config().get("launcher.concurrent_downloads", 8))
    bus.emit("install.step", {"version": version_id, "step": "metadata"})
    data = load_version_json(version_id)

    # Client jar lives with the jar-owning version (vanilla parent for loaders).
    jar_owner = data.get("jar", data["id"])
    client = data.get("downloads", {}).get("client")
    if client:
        bus.emit("install.step", {"version": version_id, "step": "client-jar"})
        download(
            client["url"],
            client_jar_path(jar_owner),
            sha1=client.get("sha1"),
            size=client.get("size"),
        )

    bus.emit("install.step", {"version": version_id, "step": "libraries"})
    classpath_jobs, native_jobs = collect_libraries(data)
    download_many(classpath_jobs + native_jobs, workers=workers)
    extract_natives(data, native_jobs)

    install_assets(data, workers=workers)

    logging_cfg = data.get("logging", {}).get("client", {}).get("file")
    if logging_cfg:
        download(
            logging_cfg["url"],
            paths.assets_dir() / "log_configs" / logging_cfg["id"],
            sha1=logging_cfg.get("sha1"),
        )

    bus.emit("install.step", {"version": version_id, "step": "done"})
    return data


def installed_versions() -> list[str]:
    root = paths.versions_dir()
    if not root.exists():
        return []
    return sorted(
        p.name for p in root.iterdir() if (p / f"{p.name}.json").exists()
    )

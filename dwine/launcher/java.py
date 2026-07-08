"""Java runtime discovery and management.

Finds a suitable Java for each Minecraft version (old versions need 8,
1.17 needs 16+, 1.18+ needs 17+, 1.20.5+ needs 21+) and can download a
managed Adoptium (Temurin) runtime when nothing suitable is installed.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Any

from ..core import paths
from ..core.http import download, get_json
from .rules import current_arch, current_os

ADOPTIUM_API = "https://api.adoptium.net/v3"


def required_major(version_data: dict[str, Any]) -> int:
    """Java major version a Minecraft version JSON asks for."""
    java = version_data.get("javaVersion")
    if java and java.get("majorVersion"):
        return int(java["majorVersion"])
    return 8


def _java_version_of(java_bin: str) -> int | None:
    try:
        out = subprocess.run(
            [java_bin, "-version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = out.stderr + out.stdout
    match = re.search(r'version "(\d+)(?:\.(\d+))?', text)
    if not match:
        return None
    major = int(match.group(1))
    if major == 1 and match.group(2):  # "1.8.0_392" style
        major = int(match.group(2))
    return major


def _candidate_javas() -> list[str]:
    candidates: list[str] = []
    if os.environ.get("JAVA_HOME"):
        exe = "java.exe" if sys.platform == "win32" else "java"
        candidates.append(str(Path(os.environ["JAVA_HOME"]) / "bin" / exe))
    found = shutil.which("java")
    if found:
        candidates.append(found)
    # Managed runtimes downloaded by Dwine.
    if paths.java_dir().exists():
        for runtime in paths.java_dir().iterdir():
            for exe_rel in ("bin/java", "bin/java.exe", "Contents/Home/bin/java"):
                exe = runtime / exe_rel
                if exe.exists():
                    candidates.append(str(exe))
    return candidates


def find_java(major: int) -> str | None:
    """Best installed java binary matching the required major version."""
    exact, higher = None, None
    for candidate in _candidate_javas():
        version = _java_version_of(candidate)
        if version is None:
            continue
        if version == major:
            exact = exact or candidate
        elif version > major and major >= 16:
            # Modern MC runs fine on newer LTS; old MC (8) must stay on 8.
            higher = higher or candidate
    return exact or higher


def install_java(major: int) -> str:
    """Download a Temurin JRE into Dwine's managed runtime directory."""
    os_name = {"windows": "windows", "osx": "mac", "linux": "linux"}[current_os()]
    arch = {"x64": "x64", "arm64": "aarch64", "x86": "x86"}.get(current_arch(), "x64")
    releases = get_json(
        f"{ADOPTIUM_API}/assets/latest/{major}/hotspot",
        params={"os": os_name, "architecture": arch, "image_type": "jre"},
    )
    if not releases:
        raise RuntimeError(f"no Temurin JRE {major} available for {os_name}/{arch}")
    package = releases[0]["binary"]["package"]
    archive = paths.cache_dir() / package["name"]
    download(package["link"], archive)
    target = paths.java_dir() / f"temurin-{major}"
    target.mkdir(parents=True, exist_ok=True)
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(target)
    else:
        with tarfile.open(archive) as tf:
            tf.extractall(target)
    # Archives contain one wrapper directory; flatten the search below.
    for exe_rel in ("bin/java", "bin/java.exe", "Contents/Home/bin/java"):
        for inner in [target, *target.iterdir()]:
            exe = inner / exe_rel
            if exe.exists():
                return str(exe)
    raise RuntimeError(f"java binary not found after extracting {package['name']}")


def ensure_java(version_data: dict[str, Any], configured_path: str = "") -> str:
    """Return a java binary for this version, downloading one if needed."""
    if configured_path:
        return configured_path
    major = required_major(version_data)
    found = find_java(major)
    if found:
        return found
    return install_java(major)

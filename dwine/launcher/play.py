"""The Play button: everything that happens between click and game start.

1. Resolve the Minecraft version (and mod loader version) for the profile
2. Install/verify the version, libraries, assets, natives
3. Launch, streaming logs onto the event bus
"""

from __future__ import annotations

import subprocess
from typing import Any

from ..core.config import get_config
from . import install, launch, manifest
from .loaders import ensure_loader
from .profiles import Profile


def prepare(profile: Profile) -> dict[str, Any]:
    """Install everything the profile needs; returns merged version JSON."""
    mc_version = profile.version or manifest.latest_release()
    if not profile.version:
        profile.version = mc_version

    version_id = ensure_loader(profile.loader, mc_version, profile.loader_version)
    return install.install_version(version_id)


def launch_profile(
    profile: Profile,
    account: dict[str, Any],
    server: str | None = None,
) -> subprocess.Popen:
    server = server or (profile.server or None)
    version_data = prepare(profile)

    cfg = get_config()
    extra_jvm: list[str] = list(profile.jvm_args)
    if profile.memory_mb:
        extra_jvm.append(f"-Xmx{profile.memory_mb}M")

    if cfg.get("performance.auto_clean.enabled", True):
        from ..tools.cleaner import clean_profile

        clean_profile(profile, dry_run=False)

    return launch.run(
        version_data,
        profile.game_dir,
        account,
        server=server,
        profile_name=profile.name,
        extra_jvm_args=extra_jvm,
    )

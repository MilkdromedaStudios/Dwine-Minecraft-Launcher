"""The Play button: everything that happens between click and game start.

1. Resolve the Minecraft version (and mod loader version) for the profile
2. Install/verify the version, libraries, assets, natives
3. Apply the safety policy for the launch target (see features.safety)
4. Sync feature mods to the effective feature set
5. Render the Dwine theme resource pack + HUD/crosshair configs
6. Launch, streaming logs onto the event bus
"""

from __future__ import annotations

import subprocess
from typing import Any

from ..content.mods import ModManager
from ..content.presets import install_preset
from ..core.config import get_config
from ..core.events import bus
from ..features import registry, safety
from ..features.crosshair import PRESETS as CROSSHAIR_PRESETS, Crosshair, save_config
from ..features.hud import HudLayout
from ..theme import mcpack
from ..theme.themes import load_theme
from . import install, launch, manifest
from .loaders import ensure_loader
from .profiles import Profile


def prepare(profile: Profile, sync_mods: bool = True) -> dict[str, Any]:
    """Install everything the profile needs; returns merged version JSON."""
    mc_version = profile.version or manifest.latest_release()
    if not profile.version:
        profile.version = mc_version

    version_id = ensure_loader(profile.loader, mc_version, profile.loader_version)
    version_data = install.install_version(version_id)

    if sync_mods and profile.content_preset:
        install_preset(profile, profile.content_preset)
    return version_data


def _sync_feature_mods(profile: Profile, enabled: dict[str, bool], server: str | None) -> None:
    """Install Modrinth-backed features that are enabled but missing."""
    if profile.loader == "vanilla":
        return  # mods need a loader; theme/launcher features still work
    manager = ModManager(profile)
    competitive = bool(server) and safety.is_competitive(server)
    installed = manager.installed()
    for fid, feature in registry.FEATURES.items():
        if feature.kind != "mod" or not enabled.get(fid):
            continue
        slug = feature.modrinth_slug
        if competitive and feature.competitive_alternative:
            slug = feature.competitive_alternative
        if not slug or slug in installed:
            continue
        try:
            manager.install(slug)
        except LookupError:
            bus.emit(
                "install.step",
                {"step": "feature-skip",
                 "detail": f"{fid}: no build for {profile.version}"},
            )


def _apply_theme(profile: Profile) -> None:
    cfg = get_config()
    if not cfg.get("theme.apply_in_game", True):
        return
    theme = load_theme(cfg.get("theme.name", "dwine-dark"))
    crosshair_cfg = cfg.get("crosshair", {}) or {}
    preset = crosshair_cfg.get("preset", "default")
    crosshair = (
        Crosshair.from_dict(crosshair_cfg.get("custom", {}))
        if preset == "custom"
        else CROSSHAIR_PRESETS.get(preset, Crosshair())
    )
    try:
        mcpack.build_pack(
            theme, profile.version, profile.resourcepacks_dir, crosshair
        )
        mcpack.enable_in_options(profile.game_dir)
    except ImportError:
        bus.emit(
            "install.step",
            {"step": "theme-skip", "detail": "Pillow not installed; run "
             "pip install dwine[full] for in-game theming"},
        )
    save_config(crosshair, profile.game_dir)
    HudLayout.load(profile.game_dir).save(profile.game_dir)


def launch_profile(
    profile: Profile,
    account: dict[str, Any],
    server: str | None = None,
) -> subprocess.Popen:
    server = server or (profile.server or None)
    version_data = prepare(profile)

    # Safety policy is applied to a *copy* of the feature map for this
    # launch; user settings themselves are never rewritten.
    enabled = registry.enabled_features(get_config())
    enforcements = safety.enforce(enabled, server)
    for action in enforcements:
        bus.emit(
            "notify",
            {"level": "info",
             "text": f"Safety: {action.feature_id} — {action.reason}"},
        )

    _sync_feature_mods(profile, enabled, server)
    _apply_theme(profile)

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

"""One-click content presets.

A preset is a curated list of Modrinth slugs. Installation is
version-aware: each mod is resolved against the profile's exact
Minecraft version and loader, and mods that don't exist for that
version (e.g. Starlight on modern versions where it's built into
vanilla) are skipped gracefully instead of breaking the install.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.events import bus
from ..launcher.profiles import Profile
from .mods import ModManager


@dataclass
class Preset:
    name: str
    description: str
    mods: list[str]
    optional: list[str] = field(default_factory=list)


PRESETS: dict[str, Preset] = {
    "performance": Preset(
        name="Performance",
        description="The Dwine FPS stack — rendering, tick, memory and "
        "lighting optimizations.",
        mods=[
            "sodium",  # rendering engine
            "lithium",  # game tick optimization
            "ferrite-core",  # memory usage
            "entityculling",  # skip rendering hidden entities
            "starlight",  # light engine rewrite (older versions)
            "memoryleakfix",  # memory leak fixes
            "krypton",  # networking stack
            "dynamic-fps",  # save GPU when unfocused
            "modernfix",  # broad performance + launch time
            "immediatelyfast",  # immediate-mode rendering batching
            "c2me-fabric",  # multi-threaded chunk loading
        ],
        optional=[
            "iris",  # shaders (loads only if you use them)
            "lazydfu",  # faster startup (older versions)
        ],
    ),
    "pvp": Preset(
        name="PvP",
        description="Competitive-legal QoL: input display, latency info, "
        "clean visuals. No combat modification of any kind.",
        mods=[
            "sodium",
            "lithium",
            "krypton",
            "appleskin",  # food/saturation indicators
            "zoomify",  # optifine-style zoom
        ],
        optional=[
            "toggle-sprint-display",
            "reeses-sodium-options",
        ],
    ),
    "skyblock": Preset(
        name="Hypixel Skyblock",
        description="Skyblock information overlays that follow Hypixel's "
        "allowed-modifications policy.",
        mods=[
            "skyblocker-liap",  # Skyblock utilities (Fabric)
        ],
        optional=[
            "sodium",
            "ferrite-core",
        ],
    ),
    "shaders": Preset(
        name="Shaders",
        description="Iris shader stack with performance support mods.",
        mods=[
            "sodium",
            "iris",
            "ferrite-core",
        ],
        optional=["lithium", "entityculling"],
    ),
}


def install_preset(profile: Profile, preset_name: str) -> dict[str, list[str]]:
    """Install a preset into a profile.

    Returns ``{"installed": [...], "skipped": [...]}`` where skipped mods
    simply have no build for this Minecraft version/loader — that is
    expected and safe (many optimizations merged into newer versions).
    """
    preset = PRESETS[preset_name]
    manager = ModManager(profile)
    installed: list[str] = []
    skipped: list[str] = []
    for slug in preset.mods + preset.optional:
        required = slug in preset.mods
        try:
            installed += manager.install(slug)
        except LookupError:
            skipped.append(slug)
            bus.emit(
                "install.step",
                {
                    "step": "preset-skip",
                    "detail": f"{slug} has no {profile.version} build"
                    + (" (required)" if required else " (optional)"),
                },
            )
        except Exception:
            if required:
                raise
            skipped.append(slug)
    return {"installed": installed, "skipped": skipped}

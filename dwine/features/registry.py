"""The Dwine feature catalog.

Every toggle the client exposes lives here, with enough metadata for the
UI, the installer, and the safety engine. Nothing in this catalog gives
a gameplay advantage: it's information display, cosmetics, and comfort.

Slugs point at well-known open-source Modrinth projects; ``fallback_query``
is used to re-locate a project if a slug ever changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Behavioral flags consumed by dwine.features.safety
FLAG_INPUT_AUTOMATION = "input_automation"  # simulates clicks/keys
FLAG_RADAR_LIKE = "radar_like"  # reveals entity/cave info


@dataclass(frozen=True)
class Feature:
    id: str
    name: str
    description: str
    category: str  # performance | hud | visual | utility | hypixel | media
    kind: str  # mod | theme | launcher | companion | bundled
    modrinth_slug: str = ""
    fallback_query: str = ""
    default_enabled: bool = False
    flags: tuple[str, ...] = ()
    # Installed instead of `modrinth_slug` on competitive networks.
    competitive_alternative: str = ""
    options: dict = field(default_factory=dict)


FEATURES: dict[str, Feature] = {
    f.id: f
    for f in [
        # -- performance ------------------------------------------------
        Feature(
            "fps_boost",
            "FPS Boost",
            "Installs the Dwine optimization stack (Sodium, Lithium, "
            "FerriteCore, Entity Culling, ModernFix …) matched to your version.",
            "performance",
            "mod",
            modrinth_slug="sodium",
            fallback_query="sodium",
            default_enabled=True,
        ),
        Feature(
            "threaded_chunks",
            "Multi-threaded chunk loading",
            "C2ME parallelizes chunk generation and loading across CPU cores.",
            "performance",
            "mod",
            modrinth_slug="c2me-fabric",
            fallback_query="c2me",
        ),
        Feature(
            "shader_support",
            "Iris shader support",
            "High-performance shader pipeline (Iris) with one-click packs.",
            "performance",
            "mod",
            modrinth_slug="iris",
            fallback_query="iris shaders",
        ),
        Feature(
            "dynamic_fps",
            "Dynamic FPS",
            "Drops GPU usage when the window is unfocused or minimized.",
            "performance",
            "mod",
            modrinth_slug="dynamic-fps",
            fallback_query="dynamic fps",
            default_enabled=True,
        ),
        # -- HUD ----------------------------------------------------------
        Feature(
            "custom_hud",
            "Custom HUD",
            "Drag-and-drop HUD editor: place, scale and restyle every element.",
            "hud",
            "companion",
            default_enabled=True,
        ),
        Feature(
            "keystrokes",
            "Keystrokes",
            "Shows WASD/mouse input on screen — display only.",
            "hud",
            "mod",
            modrinth_slug="keystrokes",
            fallback_query="keystrokes",
        ),
        Feature(
            "stats_display",
            "FPS / ping / CPS / memory display",
            "Live performance and connection stats as HUD elements.",
            "hud",
            "companion",
            default_enabled=True,
        ),
        Feature(
            "armor_status",
            "Armor & status HUD",
            "Armor durability, potion effects and held-item status on screen.",
            "hud",
            "mod",
            fallback_query="armor hud durability",
        ),
        Feature(
            "saturation_indicators",
            "Saturation & food info",
            "AppleSkin-style hunger, saturation and exhaustion indicators.",
            "hud",
            "mod",
            modrinth_slug="appleskin",
            fallback_query="appleskin",
            default_enabled=True,
        ),
        Feature(
            "compass_overlay",
            "Compass overlay",
            "A sleek direction ribbon with waypoint markers.",
            "hud",
            "mod",
            fallback_query="compass hud overlay",
        ),
        Feature(
            "custom_crosshair",
            "Custom crosshair",
            "Full crosshair editor: shape, size, color, outline, animation.",
            "visual",
            "theme",
            default_enabled=True,
        ),
        # -- visual ---------------------------------------------------------
        Feature(
            "in_game_theme",
            "Dwine in-game theme",
            "Reskins Minecraft's buttons, menus, chat and HUD with your "
            "launcher theme via an auto-generated resource pack.",
            "visual",
            "theme",
            default_enabled=True,
        ),
        Feature(
            "item_physics",
            "Item physics",
            "Dropped items tumble and lie flat, physics-style. Cosmetic only.",
            "visual",
            "mod",
            modrinth_slug="physicsmod",
            fallback_query="physics mod",
        ),
        Feature(
            "item_resize",
            "Item resize",
            "Scale dropped-item render size from 0–1000%%, per rarity tier. "
            "Client-side rendering only.",
            "visual",
            "companion",
            options={"scale_percent": 100, "per_tier": {}},
        ),
        Feature(
            "motion_blur",
            "Motion blur",
            "Smooth camera motion blur with adjustable strength.",
            "visual",
            "mod",
            fallback_query="motion blur",
        ),
        Feature(
            "hit_color",
            "Hit color",
            "Customize the red damage tint on entities you hit. Visual only.",
            "visual",
            "mod",
            fallback_query="hit color overlay",
        ),
        Feature(
            "custom_animations",
            "Custom animations",
            "First-person swing/block/hit animation styles. Purely visual — "
            "attack timing and hit detection are untouched.",
            "visual",
            "mod",
            fallback_query="first person animations",
        ),
        Feature(
            "particle_customizer",
            "Particle customizer",
            "Multiply, recolor or mute particle effects.",
            "visual",
            "mod",
            fallback_query="particle effects customize",
        ),
        Feature(
            "fullbright",
            "Fullbright",
            "Maximum gamma — identical to turning brightness past 100%%. "
            "Widely allowed; it's the vanilla brightness setting, extended.",
            "visual",
            "companion",
            options={"gamma": 16.0},
        ),
        # -- utility ---------------------------------------------------------
        Feature(
            "zoom",
            "Zoom",
            "OptiFine-style zoom key with smooth interpolation (Zoomify).",
            "utility",
            "mod",
            modrinth_slug="zoomify",
            fallback_query="zoomify zoom",
            default_enabled=True,
        ),
        Feature(
            "toggle_sprint",
            "Toggle sprint",
            "Sprint as a toggle with an on-screen state indicator.",
            "utility",
            "mod",
            fallback_query="toggle sprint display",
            default_enabled=True,
        ),
        Feature(
            "minimap",
            "Minimap & waypoints",
            "Xaero's minimap with waypoints and death markers. On competitive "
            "networks Dwine installs the Fair-Play build (no cave map, no "
            "entity radar) automatically.",
            "utility",
            "mod",
            modrinth_slug="xaeros-minimap",
            fallback_query="xaero minimap",
            flags=(FLAG_RADAR_LIKE,),
            competitive_alternative="xaeros-minimap-fair",
        ),
        Feature(
            "death_waypoints",
            "Death waypoints",
            "Automatic waypoint where you died, with distance readout.",
            "utility",
            "bundled",  # provided by the minimap feature
        ),
        Feature(
            "skip_death_screen",
            "Skip death screen",
            "Respawn instantly without clicking through the death screen.",
            "utility",
            "mod",
            fallback_query="instant respawn",
        ),
        Feature(
            "no_friend_damage",
            "Friend guard",
            "Suppresses *your own* attack input against marked friends so you "
            "never hit them by accident. Only restricts you — it cannot "
            "change what the server does.",
            "utility",
            "companion",
        ),
        Feature(
            "auto_clicker",
            "Auto clicker (singleplayer only)",
            "Holds repeated clicks for AFK-safe singleplayer tasks. Hard-"
            "disabled on every multiplayer server: input automation breaks "
            "the rules of Hypixel and most networks, so Dwine physically "
            "does not run it outside singleplayer.",
            "utility",
            "companion",
            flags=(FLAG_INPUT_AUTOMATION,),
            options={"cps": 8, "singleplayer_only": True},
        ),
        Feature(
            "screenshot_manager",
            "Screenshot manager",
            "Gallery, editor, and quick sharing for your screenshots.",
            "utility",
            "launcher",
            default_enabled=True,
        ),
        Feature(
            "replay",
            "Replay system",
            "Record and re-watch sessions with the Replay Mod (Hypixel-allowed).",
            "utility",
            "mod",
            modrinth_slug="replaymod",
            fallback_query="replay mod",
        ),
        # -- hypixel ---------------------------------------------------------
        Feature(
            "skyblock_utilities",
            "Skyblock utilities",
            "Waypoints, dungeon map, ability timers, drop trackers and "
            "overlays via Skyblocker — built to Hypixel's mod policy.",
            "hypixel",
            "mod",
            modrinth_slug="skyblocker-liap",
            fallback_query="skyblocker",
        ),
        Feature(
            "bedwars_utilities",
            "Bedwars utilities",
            "Resource timers and team overlays using only visible scoreboard "
            "data. No stat advantages, no automation.",
            "hypixel",
            "companion",
        ),
        Feature(
            "level_head",
            "Level head",
            "Shows Hypixel network levels above players (public API data).",
            "hypixel",
            "mod",
            fallback_query="levelhead hypixel",
        ),
        Feature(
            "auto_gg",
            "Auto GG",
            "Says 'gg' when a game ends — explicitly permitted by Hypixel.",
            "hypixel",
            "mod",
            fallback_query="autogg",
        ),
        Feature(
            "nick_hider",
            "Nick hider",
            "Hides your own name/skin locally for streaming privacy.",
            "hypixel",
            "mod",
            fallback_query="nick hider",
        ),
        Feature(
            "party_hud",
            "Party HUD",
            "Party member list with health from visible packets only.",
            "hypixel",
            "companion",
        ),
        Feature(
            "scoreboard_enhancements",
            "Scoreboard enhancements",
            "Restyle the sidebar: numbers off, custom colors, compact mode.",
            "hypixel",
            "companion",
            default_enabled=True,
        ),
        # -- media -------------------------------------------------------------
        Feature(
            "spotify_miniplayer",
            "Spotify miniplayer",
            "Now-playing overlay with controls, powered by Spotify Connect.",
            "media",
            "launcher",
        ),
        Feature(
            "discord_rpc",
            "Discord Rich Presence",
            "Shows your version/server/profile in Discord.",
            "media",
            "launcher",
            default_enabled=True,
        ),
        Feature(
            "capes",
            "Dwine capes",
            "Client-side cosmetic capes, visible to you and other Dwine users.",
            "media",
            "companion",
            default_enabled=True,
        ),
    ]
}

CATEGORIES = ("performance", "hud", "visual", "utility", "hypixel", "media")


def by_category(category: str) -> list[Feature]:
    return [f for f in FEATURES.values() if f.category == category]


def get(feature_id: str) -> Feature:
    return FEATURES[feature_id]


def enabled_features(config) -> dict[str, bool]:
    """Effective enabled-map: user settings over catalog defaults."""
    state = {}
    user = config.get("features", {}) or {}
    for fid, feature in FEATURES.items():
        entry = user.get(fid)
        if isinstance(entry, dict):
            state[fid] = bool(entry.get("enabled", feature.default_enabled))
        elif isinstance(entry, bool):
            state[fid] = entry
        else:
            state[fid] = feature.default_enabled
    return state

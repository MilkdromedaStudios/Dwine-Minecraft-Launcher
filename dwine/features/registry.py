"""The Dwine feature catalog.

Every toggle the client exposes lives here, with enough metadata for the
UI, the installer, and the safety engine. Nothing in this catalog gives
a gameplay advantage: it's information display, cosmetics, and comfort.

Each feature also declares its **settings** — the small knobs that tune
its behavior (sliders, colors, choices…). The launcher edits them, and
on every launch the effective feature map + settings are written to
``config/dwine/features.json`` inside the profile's game directory,
where the Dwine companion mod renders them **in game**. The launcher is
just the remote control; the features live in the game.

Slugs point at well-known open-source Modrinth projects; ``fallback_query``
is used to re-locate a project if a slug ever changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Behavioral flags consumed by dwine.features.safety
FLAG_INPUT_AUTOMATION = "input_automation"  # simulates clicks/keys
FLAG_RADAR_LIKE = "radar_like"  # reveals info the vanilla client doesn't show

SETTING_KINDS = ("toggle", "slider", "color", "choice", "text")


@dataclass(frozen=True)
class Setting:
    """One tunable knob on a feature (rendered by the Features page)."""

    id: str
    label: str
    kind: str  # one of SETTING_KINDS
    default: Any = None
    minimum: int = 0
    maximum: int = 100
    step: int = 1
    choices: tuple[str, ...] = ()
    suffix: str = ""  # display suffix for sliders ("%", "px", "s"…)

    def __post_init__(self) -> None:
        if self.kind not in SETTING_KINDS:
            raise ValueError(f"unknown setting kind {self.kind!r}")
        if self.kind == "choice" and self.default not in self.choices:
            raise ValueError(f"{self.id}: default {self.default!r} not in choices")


# Shorthand constructors keep the catalog below readable.
def _toggle(sid: str, label: str, default: bool = False) -> Setting:
    return Setting(sid, label, "toggle", default)


def _slider(sid: str, label: str, default: int, minimum: int, maximum: int,
            step: int = 1, suffix: str = "") -> Setting:
    return Setting(sid, label, "slider", default, minimum, maximum, step,
                   suffix=suffix)


def _color(sid: str, label: str, default: str = "#FFFFFF") -> Setting:
    return Setting(sid, label, "color", default)


def _choice(sid: str, label: str, default: str, *choices: str) -> Setting:
    return Setting(sid, label, "choice", default, choices=tuple(choices))


def _text(sid: str, label: str, default: str = "") -> Setting:
    return Setting(sid, label, "text", default)


@dataclass(frozen=True)
class Feature:
    id: str
    name: str
    description: str
    category: str  # see CATEGORIES
    kind: str  # mod | theme | launcher | companion | bundled
    modrinth_slug: str = ""
    fallback_query: str = ""
    default_enabled: bool = False
    flags: tuple[str, ...] = ()
    # Installed instead of `modrinth_slug` on competitive networks.
    competitive_alternative: str = ""
    options: dict = field(default_factory=dict)
    settings: tuple[Setting, ...] = ()


_POSITIONS = ("top_left", "top_center", "top_right", "middle_left",
              "middle_right", "bottom_left", "bottom_center", "bottom_right")


FEATURES: dict[str, Feature] = {
    f.id: f
    for f in [
        # ==================================================================
        # PERFORMANCE
        # ==================================================================
        Feature(
            "fps_boost",
            "FPS Boost",
            "Installs the Dwine optimization stack (Sodium, Lithium, "
            "FerriteCore, ModernFix …) matched to your version.",
            "performance", "mod",
            modrinth_slug="sodium", fallback_query="sodium",
            default_enabled=True,
            settings=(
                _choice("stack", "Optimization stack", "full", "light", "full"),
                _toggle("keep_updated", "Keep the stack updated", True),
            ),
        ),
        Feature(
            "memory_cleaner",
            "Memory Cleaner",
            "Trims unused caches and hints the garbage collector while you "
            "play, smoothing out memory spikes.",
            "performance", "companion",
            settings=(
                _slider("interval_seconds", "Clean every", 300, 60, 1800, 30, "s"),
                _toggle("notify", "Show a toast after each clean", False),
                _slider("target_usage", "Trigger above heap usage", 80, 50, 95, 5, "%"),
            ),
        ),
        Feature(
            "entity_culling",
            "Entity Culling",
            "Skips rendering entities that are fully hidden behind blocks.",
            "performance", "mod",
            modrinth_slug="entityculling", fallback_query="entity culling",
            default_enabled=True,
            settings=(
                _toggle("tick_culling", "Also skip ticking hidden entities", False),
                _slider("check_distance", "Culling check distance", 64, 16, 128, 8, " blocks"),
            ),
        ),
        Feature(
            "particle_culling",
            "Particle Culling",
            "Stops rendering particles that are outside the view or too far "
            "away, with a hard cap you control.",
            "performance", "companion",
            settings=(
                _slider("max_particles", "Particle cap", 4000, 500, 16000, 500),
                _slider("max_distance", "Max particle distance", 32, 8, 128, 8, " blocks"),
            ),
        ),
        Feature(
            "chunk_culling",
            "Chunk Culling",
            "Skips rendering chunk sections the camera cannot see.",
            "performance", "companion",
            settings=(
                _toggle("aggressive", "Aggressive mode (more FPS, rare pop-in)", False),
            ),
        ),
        Feature(
            "threaded_chunks",
            "Multi-threaded chunk loading",
            "C2ME parallelizes chunk generation and loading across CPU cores.",
            "performance", "mod",
            modrinth_slug="c2me-fabric", fallback_query="c2me",
            settings=(
                _slider("thread_percent", "CPU threads to use", 75, 25, 100, 25, "%"),
            ),
        ),
        Feature(
            "dynamic_fps",
            "Dynamic FPS",
            "Drops GPU usage when the window is unfocused or minimized.",
            "performance", "mod",
            modrinth_slug="dynamic-fps", fallback_query="dynamic fps",
            default_enabled=True,
            settings=(
                _slider("unfocused_fps", "FPS while unfocused", 15, 1, 60, 1),
                _toggle("pause_when_hidden", "Fully pause rendering when minimized", True),
            ),
        ),
        Feature(
            "shader_support",
            "Iris shader support",
            "High-performance shader pipeline (Iris) with one-click packs.",
            "performance", "mod",
            modrinth_slug="iris", fallback_query="iris shaders",
            settings=(
                _toggle("shadows", "Shader shadows", True),
            ),
        ),
        Feature(
            "shadow_toggle",
            "Shadow Toggle",
            "Turn entity shadows off (or keep only your own) for extra frames.",
            "performance", "companion",
            settings=(
                _toggle("hide_entity_shadows", "Hide entity shadows", True),
                _toggle("keep_own_shadow", "Keep your own shadow", False),
            ),
        ),
        Feature(
            "vsync_toggle",
            "VSync Toggle",
            "Quick VSync switch with an optional FPS cap when it's off.",
            "performance", "companion",
            settings=(
                _slider("fps_cap", "FPS cap when VSync is off (0 = unlimited)",
                        0, 0, 540, 10),
            ),
        ),
        Feature(
            "antialiasing",
            "Anti-Aliasing Toggle",
            "Smooths jagged edges; pick the sample count that suits your GPU.",
            "performance", "companion",
            settings=(
                _choice("samples", "Samples", "4x", "2x", "4x", "8x"),
            ),
        ),
        Feature(
            "mipmap_control",
            "Mipmap Slider",
            "Fine-grained mipmap levels for crisper or smoother distant textures.",
            "performance", "companion",
            settings=(
                _slider("levels", "Mipmap levels", 4, 0, 4, 1),
            ),
        ),
        Feature(
            "fog_toggle",
            "Fog Toggle",
            "Hides terrain and dimension fog rendering — purely visual.",
            "performance", "companion",
            settings=(
                _toggle("terrain_fog", "Hide terrain fog", True),
                _toggle("nether_fog", "Hide Nether fog", True),
                _toggle("water_fog", "Reduce underwater fog", False),
            ),
        ),
        Feature(
            "render_distance",
            "Render Distance Slider",
            "Per-profile render distance override, applied on launch.",
            "performance", "companion",
            settings=(
                _slider("chunks", "Render distance", 12, 2, 32, 1, " chunks"),
                _slider("simulation", "Simulation distance", 12, 5, 32, 1, " chunks"),
            ),
        ),
        Feature(
            "entity_distance",
            "Entity Slider",
            "Entity render-distance percentage, from potato to cinematic.",
            "performance", "companion",
            settings=(
                _slider("percent", "Entity distance", 100, 10, 500, 10, "%"),
            ),
        ),
        Feature(
            "animation_toggle",
            "Animation Toggle",
            "Turn individual world animations (water, fire, portals…) off "
            "for extra performance.",
            "performance", "companion",
            settings=(
                _toggle("water", "Animate water", True),
                _toggle("lava", "Animate lava", True),
                _toggle("fire", "Animate fire", True),
                _toggle("portal", "Animate portals", True),
                _toggle("smooth_lighting", "Smooth lighting", True),
            ),
        ),
        Feature(
            "fps_graph",
            "FPS Graph",
            "A tiny rolling frame-time graph so you can spot stutters.",
            "performance", "companion",
            settings=(
                _slider("width", "Graph width", 120, 60, 320, 10, "px"),
                _slider("history_seconds", "History", 10, 3, 60, 1, "s"),
                _color("color", "Graph color", "#3DDC97"),
            ),
        ),
        Feature(
            "chunk_graph",
            "Chunk Graph",
            "Graphs chunk updates per second — handy for tuning render distance.",
            "performance", "companion",
            settings=(
                _slider("width", "Graph width", 120, 60, 320, 10, "px"),
                _color("color", "Graph color", "#4F8CFF"),
            ),
        ),

        # ==================================================================
        # HUD — info elements (all display-only; place them with the HUD editor)
        # ==================================================================
        Feature(
            "custom_hud",
            "Custom HUD Editor",
            "Every HUD element is moveable: drag, scale and restyle in the "
            "launcher's editor or in game with the editor key.",
            "hud", "companion",
            default_enabled=True,
            settings=(
                _toggle("in_game_editor", "In-game editor (opens with a key)", True),
                _text("editor_key", "Editor key", "RSHIFT"),
                _toggle("snap_to_grid", "Snap to grid", True),
                _slider("global_scale", "HUD scaling", 100, 50, 200, 5, "%"),
                _slider("global_opacity", "HUD opacity", 100, 20, 100, 5, "%"),
                _toggle("backgrounds", "HUD backgrounds", True),
                _color("background_color", "Background color", "#101418"),
            ),
        ),
        Feature(
            "fps_counter",
            "FPS Counter",
            "Live frames-per-second readout.",
            "hud", "companion",
            default_enabled=True,
            settings=(
                _toggle("show_min", "Show 1% lows", False),
                _color("color", "Text color", "#FFFFFF"),
                _toggle("label", "Show the 'FPS' label", True),
            ),
        ),
        Feature(
            "cps_counter",
            "CPS Counter",
            "Clicks-per-second display for either or both mouse buttons.",
            "hud", "companion",
            settings=(
                _choice("buttons", "Buttons to track", "both", "left", "right", "both"),
                _slider("window_seconds", "Averaging window", 1, 1, 5, 1, "s"),
                _color("color", "Text color", "#FFFFFF"),
            ),
        ),
        Feature(
            "ping_display",
            "Ping Display",
            "Your current latency to the server, straight from the tab list.",
            "hud", "companion",
            settings=(
                _slider("refresh_seconds", "Refresh every", 2, 1, 10, 1, "s"),
                _toggle("color_coded", "Color by quality (green/yellow/red)", True),
            ),
        ),
        Feature(
            "coordinates_hud",
            "Coordinates HUD",
            "X / Y / Z position readout, with optional Nether conversion.",
            "hud", "companion",
            settings=(
                _toggle("compact", "Compact one-line mode", True),
                _toggle("show_dimension", "Show dimension", False),
                _toggle("nether_coords", "Show Nether-converted coordinates", False),
                _toggle("show_biome", "Show biome", False),
            ),
        ),
        Feature(
            "clock_hud",
            "Clock HUD",
            "Real-world clock, in-game time, or both.",
            "hud", "companion",
            settings=(
                _choice("mode", "Clock mode", "real", "real", "ingame", "both"),
                _toggle("twenty_four_hour", "24-hour format", True),
                _toggle("show_seconds", "Show seconds", False),
            ),
        ),
        Feature(
            "compass_hud",
            "Compass HUD",
            "A sleek direction ribbon with cardinal points and waypoint markers.",
            "hud", "companion",
            settings=(
                _slider("width", "Ribbon width", 220, 120, 480, 10, "px"),
                _toggle("show_degrees", "Show exact degrees", True),
                _toggle("show_waypoints", "Show waypoint markers", True),
            ),
        ),
        Feature(
            "armor_hud",
            "Armor HUD",
            "Armor pieces with durability, plus your held items.",
            "hud", "companion",
            settings=(
                _choice("durability", "Durability style", "percent",
                        "percent", "absolute", "bar"),
                _toggle("vertical", "Vertical layout", True),
                _toggle("show_held_items", "Include held items", True),
                _toggle("warn_low", "Flash when durability is low", True),
            ),
        ),
        Feature(
            "potion_hud",
            "Potion HUD",
            "Active status effects with icons and remaining time.",
            "hud", "companion",
            settings=(
                _toggle("show_duration", "Show remaining time", True),
                _toggle("blink_expiring", "Blink when about to expire", True),
                _toggle("compact", "Icons only (compact)", False),
            ),
        ),
        Feature(
            "direction_hud",
            "Direction HUD",
            "Which way you're facing: N/S/E/W, full names, or degrees.",
            "hud", "companion",
            settings=(
                _choice("style", "Style", "letter", "letter", "full", "degrees"),
                _toggle("show_axis", "Show the +/- axis (e.g. 'towards +Z')", False),
            ),
        ),
        Feature(
            "speed_hud",
            "Speed HUD",
            "Your current movement speed — great for elytra and boat runs.",
            "hud", "companion",
            settings=(
                _choice("unit", "Unit", "bps", "bps", "kmh"),
                _slider("decimals", "Decimal places", 1, 0, 3, 1),
                _toggle("horizontal_only", "Ignore vertical movement", True),
            ),
        ),
        Feature(
            "stopwatch_hud",
            "Stopwatch HUD",
            "A start/stop/lap timer on a hotkey — speedrun practice, farms, races.",
            "hud", "companion",
            settings=(
                _text("hotkey", "Start/stop key", "U"),
                _toggle("show_millis", "Show milliseconds", True),
                _toggle("laps", "Enable lap times", False),
            ),
        ),
        Feature(
            "combo_counter",
            "Combo Counter",
            "Counts consecutive hits you land; resets when you take one.",
            "hud", "companion",
            settings=(
                _slider("reset_seconds", "Reset after", 3, 1, 10, 1, "s"),
                _color("highlight_color", "Highlight color", "#FFD166"),
                _toggle("show_best", "Show session best", True),
            ),
        ),
        Feature(
            "hit_delay_indicator",
            "Hit Delay Indicator",
            "Shows the vanilla attack-cooldown timer near your crosshair — "
            "an indicator only, the timing itself is untouched.",
            "hud", "companion",
            settings=(
                _choice("style", "Style", "ring", "ring", "bar", "number"),
                _toggle("attach_to_crosshair", "Attach to crosshair", True),
                _color("ready_color", "Ready color", "#3DDC97"),
            ),
        ),
        Feature(
            "block_hit_delay",
            "Block Hit Delay",
            "Shows the brief cooldown between block breaks — display only, "
            "break timing is untouched.",
            "hud", "companion",
            settings=(
                _choice("style", "Style", "bar", "bar", "number"),
                _color("color", "Indicator color", "#B18CFF"),
            ),
        ),
        Feature(
            "hit_distance",
            "Hit Distance Display",
            "Shows the measured distance of your most recent landed hit. "
            "A read-out of what already happened — nothing about combat changes.",
            "hud", "companion",
            settings=(
                _slider("decimals", "Decimal places", 2, 0, 3, 1),
                _slider("fade_seconds", "Fade out after", 3, 1, 10, 1, "s"),
            ),
        ),
        Feature(
            "keystrokes",
            "Keystrokes",
            "Shows WASD/mouse input on screen — display only.",
            "hud", "companion",
            settings=(
                _toggle("show_mouse", "Show mouse buttons", True),
                _toggle("show_spacebar", "Show spacebar", True),
                _toggle("show_cps_on_keys", "Show CPS on mouse keys", False),
                _color("key_color", "Key color", "#FFFFFF"),
                _color("pressed_color", "Pressed color", "#4F8CFF"),
            ),
        ),
        Feature(
            "saturation_hud",
            "Saturation HUD",
            "AppleSkin-style hunger, saturation and exhaustion indicators.",
            "hud", "mod",
            modrinth_slug="appleskin", fallback_query="appleskin",
            default_enabled=True,
            settings=(
                _toggle("show_exhaustion", "Show exhaustion", True),
                _toggle("show_food_values", "Show food values in tooltips", True),
            ),
        ),
        Feature(
            "server_info_hud",
            "Server Info HUD",
            "The server you're on: address, ping, player count.",
            "hud", "companion",
            settings=(
                _toggle("show_address", "Show address", True),
                _toggle("show_ping", "Show ping", True),
                _toggle("show_players", "Show player count", True),
            ),
        ),
        Feature(
            "match_timer",
            "Match Timer",
            "Counts up from the moment a round or game starts.",
            "hud", "companion",
            settings=(
                _toggle("auto_start", "Auto-start when a game begins", True),
                _toggle("show_millis", "Show milliseconds", False),
            ),
        ),
        Feature(
            "stats_display",
            "Memory & session stats",
            "Memory usage, session length and other launcher-fed stats as "
            "HUD elements.",
            "hud", "companion",
            default_enabled=True,
            settings=(
                _toggle("memory", "Show memory usage", True),
                _toggle("session_time", "Show session time", False),
            ),
        ),

        # ==================================================================
        # VISUAL
        # ==================================================================
        Feature(
            "custom_crosshair",
            "Custom Crosshair",
            "Parametric crosshair editor plus a full drawpad: paint your own "
            "pixel-perfect crosshair, rendered into the theme pack.",
            "visual", "theme",
            default_enabled=True,
            settings=(
                _slider("scale", "Crosshair scale", 100, 50, 300, 10, "%"),
                _toggle("hide_in_third_person", "Hide in third person", True),
                _toggle("hide_when_gui_open", "Hide when a GUI is open", False),
            ),
        ),
        Feature(
            "crosshair_animations",
            "Crosshair Animations",
            "Make the crosshair react: pulse or spin when you land a hit.",
            "visual", "theme",
            settings=(
                _choice("on_hit", "On-hit animation", "pulse", "none", "pulse", "spin"),
                _slider("speed", "Animation speed", 100, 25, 300, 25, "%"),
            ),
        ),
        Feature(
            "crosshair_movement",
            "Crosshair Movement",
            "Subtle crosshair sway and landing bounce as you move and jump.",
            "visual", "theme",
            settings=(
                _slider("intensity", "Movement intensity", 40, 0, 100, 5, "%"),
                _toggle("on_jump", "Bounce on landing", True),
            ),
        ),
        Feature(
            "entity_hitboxes",
            "Entity Hitboxes",
            "Restyled version of vanilla's F3+B hitbox view: your colors, "
            "your line thickness.",
            "visual", "companion",
            settings=(
                _slider("thickness", "Hitbox thickness", 2, 1, 6, 1, "px"),
                _color("color", "Hitbox color", "#FF5D73"),
                _toggle("show_eye_line", "Show eye-level line", True),
            ),
        ),
        Feature(
            "block_hitboxes",
            "Block Hitboxes",
            "Draws collision boxes of nearby interactable blocks you aim at.",
            "visual", "companion",
            settings=(
                _slider("thickness", "Line thickness", 2, 1, 6, 1, "px"),
                _color("color", "Box color", "#4F8CFF"),
            ),
        ),
        Feature(
            "block_outline",
            "Better Block Outline",
            "Replace the thin black target outline with your own style.",
            "visual", "companion",
            settings=(
                _slider("thickness", "Block outline thickness", 2, 1, 8, 1, "px"),
                _color("color", "Block outline color", "#FFFFFF"),
                _choice("style", "Style", "box", "box", "glow", "corners"),
            ),
        ),
        Feature(
            "selection_highlight",
            "Block Selection Highlight",
            "A soft glow on the block you're looking at.",
            "visual", "companion",
            settings=(
                _color("color", "Highlight color", "#4F8CFF"),
                _slider("opacity", "Highlight opacity", 30, 5, 80, 5, "%"),
            ),
        ),
        Feature(
            "block_overlay",
            "Block Overlay",
            "Fills the targeted block face with a translucent overlay.",
            "visual", "companion",
            settings=(
                _color("fill_color", "Fill color", "#B18CFF"),
                _slider("fill_opacity", "Fill opacity", 25, 5, 70, 5, "%"),
                _toggle("outline_too", "Keep the outline as well", True),
            ),
        ),
        Feature(
            "block_break_overlay",
            "Block Break Overlay",
            "Restyle the block-breaking progress: radial, percent or classic.",
            "visual", "companion",
            settings=(
                _choice("style", "Style", "radial", "vanilla", "radial", "percent"),
                _color("color", "Progress color", "#3DDC97"),
            ),
        ),
        Feature(
            "chunk_borders",
            "Chunk Borders",
            "Vanilla's F3+G chunk grid, restyled and on its own key.",
            "visual", "companion",
            settings=(
                _color("color", "Grid color", "#FFD166"),
                _toggle("show_subchunks", "Show 16×16×16 sections", False),
            ),
        ),
        Feature(
            "light_overlay",
            "Light Overlay",
            "Shows block-light levels on the ground so you can spawn-proof "
            "your base — reads only what the client already knows.",
            "visual", "companion",
            settings=(
                _choice("style", "Marker style", "cross", "cross", "number"),
                _slider("radius", "Overlay radius", 16, 4, 32, 2, " blocks"),
            ),
        ),
        Feature(
            "mob_health",
            "Mob Health Display",
            "Hearts or numbers above mobs in your line of sight.",
            "visual", "companion",
            settings=(
                _choice("style", "Style", "hearts", "hearts", "number", "bar"),
                _toggle("only_on_hit", "Only after you hit them", False),
                _slider("max_distance", "Max distance", 16, 4, 32, 2, " blocks"),
            ),
        ),
        Feature(
            "mob_nameplates",
            "Mob Nameplates",
            "Bigger, cleaner nameplates for mobs and players in view.",
            "visual", "companion",
            settings=(
                _slider("scale", "Nameplate scale", 100, 50, 200, 10, "%"),
                _toggle("show_health", "Include health", True),
                _color("background", "Background color", "#101418"),
            ),
        ),
        Feature(
            "arrow_trajectory",
            "Arrow Trajectories",
            "Previews your bow shot's arc using client-side physics. "
            "Disabled automatically on competitive networks.",
            "visual", "companion",
            flags=(FLAG_RADAR_LIKE,),
            settings=(
                _color("line_color", "Arc color", "#3DDC97"),
                _slider("max_points", "Arc length", 60, 20, 200, 10, " points"),
            ),
        ),
        Feature(
            "projectile_path",
            "Projectile Path",
            "Same preview for pearls, snowballs and potions. "
            "Disabled automatically on competitive networks.",
            "visual", "companion",
            flags=(FLAG_RADAR_LIKE,),
            settings=(
                _color("line_color", "Path color", "#B18CFF"),
                _toggle("landing_marker", "Show landing marker", True),
            ),
        ),
        Feature(
            "hit_color",
            "Hit Color Indicator",
            "Customize the red damage tint on entities you hit. Visual only.",
            "visual", "companion",
            settings=(
                _color("color", "Hit tint", "#FF5D73"),
                _slider("duration_ms", "Flash duration", 300, 100, 1000, 50, "ms"),
            ),
        ),
        Feature(
            "damage_tint",
            "Damage Tint",
            "Restyle the screen tint you see when taking damage.",
            "visual", "companion",
            settings=(
                _slider("intensity", "Tint intensity", 60, 0, 100, 5, "%"),
                _color("color", "Tint color", "#FF5D73"),
            ),
        ),
        Feature(
            "damage_particles",
            "Damage Particles",
            "Floating damage numbers and extra hit particles, rendered from "
            "health changes the client already sees.",
            "visual", "companion",
            settings=(
                _toggle("numbers", "Show damage numbers", True),
                _color("number_color", "Number color", "#FFD166"),
                _color("crit_color", "Critical color", "#FF5D73"),
            ),
        ),
        Feature(
            "better_particles",
            "Better Particles",
            "Multiply, recolor or mute particle effects — includes the "
            "particle amount slider.",
            "visual", "companion",
            settings=(
                _slider("multiplier", "Particle amount", 100, 0, 400, 10, "%"),
                _toggle("crit_recolor", "Recolor crit particles", False),
                _color("crit_color", "Crit particle color", "#FFD166"),
            ),
        ),
        Feature(
            "swing_animations",
            "Swing Animations",
            "First-person swing styles and speed. Purely visual — attack "
            "timing and hit detection are untouched.",
            "visual", "companion",
            settings=(
                _choice("style", "Swing style", "vanilla", "vanilla", "smooth", "snappy"),
                _slider("speed", "Swing speed (visual)", 100, 50, 200, 10, "%"),
            ),
        ),
        Feature(
            "old_animations",
            "Old Animations",
            "1.7-style visuals: classic rod swing, held-item position, sneak "
            "transition. Client rendering only.",
            "visual", "companion",
            settings=(
                _toggle("item_position", "Classic held-item position", True),
                _toggle("rod_swing", "Classic rod animation", True),
                _toggle("sneak_transition", "Classic sneak transition", True),
            ),
        ),
        Feature(
            "wavey_capes",
            "Wavey Capes",
            "Capes flow and ripple in the wind instead of hanging stiff.",
            "visual", "companion",
            settings=(
                _slider("wave_amount", "Wave amount", 50, 10, 100, 5, "%"),
                _choice("style", "Cloth style", "smooth", "smooth", "blocky"),
            ),
        ),
        Feature(
            "wavey_skins",
            "Wavey Skins",
            "Loose skin layers (jacket, hat overlays) sway as you move.",
            "visual", "companion",
            settings=(
                _slider("intensity", "Sway intensity", 40, 10, 100, 5, "%"),
            ),
        ),
        Feature(
            "motion_blur",
            "Motion Blur",
            "Smooth camera motion blur with adjustable strength.",
            "visual", "companion",
            settings=(
                _slider("strength", "Blur strength", 30, 5, 100, 5, "%"),
            ),
        ),
        Feature(
            "cooldown_indicator",
            "Cooldown Indicator",
            "Shows item cooldowns (pearls, chorus fruit…) as a clean radial.",
            "visual", "companion",
            settings=(
                _choice("style", "Style", "radial", "radial", "bar", "number"),
                _toggle("only_held", "Only for the held item", False),
            ),
        ),
        Feature(
            "in_game_theme",
            "Dwine in-game theme",
            "Reskins Minecraft's buttons, menus, chat and HUD with your "
            "launcher theme via an auto-generated resource pack.",
            "visual", "theme",
            default_enabled=True,
            settings=(
                _toggle("buttons", "Theme buttons and widgets", True),
                _toggle("menu_background", "Theme menu backgrounds", True),
            ),
        ),
        Feature(
            "item_physics",
            "Item physics",
            "Dropped items tumble and lie flat, physics-style. Cosmetic only.",
            "visual", "mod",
            modrinth_slug="physicsmod", fallback_query="physics mod",
            settings=(
                _slider("tumble", "Tumble amount", 60, 0, 100, 5, "%"),
            ),
        ),
        Feature(
            "custom_fonts",
            "Custom Fonts",
            "Swap the game font: clean sans, monospace, or the classic look.",
            "visual", "companion",
            settings=(
                _choice("font", "Font", "default", "default", "inter",
                        "jetbrains-mono", "unicode"),
                _toggle("shadow", "Text shadow", True),
            ),
        ),
        Feature(
            "custom_colors",
            "Custom Colors",
            "One accent palette for every Dwine element in game.",
            "visual", "companion",
            settings=(
                _toggle("use_theme", "Follow the launcher theme", True),
                _color("accent", "Accent color", "#4F8CFF"),
                _color("secondary", "Secondary color", "#B18CFF"),
            ),
        ),

        # ==================================================================
        # CHAT
        # ==================================================================
        Feature(
            "transparent_chat",
            "Transparent Chat",
            "See the world through your chat: background and text opacity.",
            "chat", "companion",
            settings=(
                _slider("background_opacity", "Chat background opacity", 25, 0, 100, 5, "%"),
                _slider("text_opacity", "Text opacity", 100, 40, 100, 5, "%"),
            ),
        ),
        Feature(
            "chat_window",
            "Chat Size & Position",
            "The chat sliders: scale, width and height, plus fine position.",
            "chat", "companion",
            settings=(
                _slider("scale", "Chat scale", 100, 50, 150, 5, "%"),
                _slider("width", "Chat width", 320, 180, 640, 10, "px"),
                _slider("height", "Chat height", 180, 90, 360, 10, "px"),
                _slider("offset_y", "Lift above hotbar", 0, 0, 120, 4, "px"),
            ),
        ),
        Feature(
            "chat_animations",
            "Chat Animations",
            "New messages slide or fade in instead of popping.",
            "chat", "companion",
            settings=(
                _choice("style", "Animation", "slide", "slide", "fade"),
                _slider("speed", "Animation speed", 100, 50, 200, 10, "%"),
            ),
        ),
        Feature(
            "chat_filter",
            "Chat Filter",
            "Hide or soften messages that match your own word list — local "
            "display filtering only.",
            "chat", "companion",
            settings=(
                _text("blocked_words", "Blocked words (comma-separated)", ""),
                _choice("action", "When matched", "hide", "hide", "blur", "replace"),
                _text("replacement", "Replacement text", "***"),
                _toggle("collapse_spam", "Collapse repeated messages", True),
            ),
        ),
        Feature(
            "chat_timestamps",
            "Chat Time Stamps",
            "Prefix every message with the time it arrived.",
            "chat", "companion",
            settings=(
                _choice("format", "Format", "HH:MM", "HH:MM", "HH:MM:SS", "12h"),
                _color("color", "Timestamp color", "#8A93A6"),
            ),
        ),
        Feature(
            "chat_heads",
            "Chat Heads",
            "Shows the sender's face next to their chat messages.",
            "chat", "companion",
            settings=(
                _slider("size", "Head size", 8, 8, 16, 1, "px"),
                _toggle("only_players", "Players only (skip server messages)", True),
            ),
        ),
        Feature(
            "better_tab",
            "Better Tab List",
            "Numeric ping, player heads, and more columns in the tab list.",
            "chat", "companion",
            settings=(
                _toggle("ping_numbers", "Numeric ping", True),
                _toggle("player_heads", "Show heads", True),
                _slider("columns", "Max columns", 4, 1, 8, 1),
            ),
        ),
        Feature(
            "auto_gg",
            "AutoGG",
            "Says 'gg' when a game ends — explicitly permitted by Hypixel.",
            "chat", "companion",
            settings=(
                _text("message", "Message", "gg"),
                _slider("delay_seconds", "Send after", 1, 0, 5, 1, "s"),
                _toggle("second_message", "Send a follow-up message", False),
                _text("second_text", "Follow-up text", "Good game!"),
            ),
        ),

        # ==================================================================
        # INTERFACE
        # ==================================================================
        Feature(
            "scoreboard_customizer",
            "Scoreboard Customizer",
            "Restyle the sidebar: numbers off, custom colors, compact mode, "
            "and your choice of screen position.",
            "interface", "companion",
            default_enabled=True,
            settings=(
                _toggle("hide_numbers", "Hide the red numbers", True),
                _slider("background_opacity", "Background opacity", 30, 0, 100, 5, "%"),
                _slider("scale", "Scale", 100, 50, 150, 5, "%"),
                _choice("position", "Scoreboard position", "middle_right", *_POSITIONS),
            ),
        ),
        Feature(
            "bossbar_customizer",
            "Bossbar Customizer",
            "Move, scale, or hide boss bars.",
            "interface", "companion",
            settings=(
                _choice("position", "Bossbar position", "top_center", *_POSITIONS),
                _slider("scale", "Scale", 100, 50, 150, 5, "%"),
                _toggle("hide", "Hide boss bars entirely", False),
            ),
        ),
        Feature(
            "hotbar_customizer",
            "Hotbar Customizer",
            "Move and restyle the hotbar and its attached bars.",
            "interface", "companion",
            settings=(
                _choice("position", "Hotbar position", "bottom_center", *_POSITIONS),
                _slider("scale", "Scale", 100, 50, 150, 5, "%"),
                _slider("background_opacity", "Background opacity", 100, 0, 100, 5, "%"),
            ),
        ),
        Feature(
            "inventory_blur",
            "Inventory Blur",
            "Softly blurs the world behind open inventories.",
            "interface", "companion",
            settings=(
                _slider("strength", "Blur strength", 50, 10, 100, 5, "%"),
            ),
        ),
        Feature(
            "inventory_animations",
            "Inventory Animations",
            "Inventories scale/fade in instead of appearing instantly.",
            "interface", "companion",
            settings=(
                _choice("style", "Style", "scale", "scale", "fade", "slide"),
                _slider("speed", "Speed", 100, 50, 200, 10, "%"),
            ),
        ),
        Feature(
            "menu_blur",
            "Menu Blur",
            "Blurred world behind the pause and settings menus.",
            "interface", "companion",
            settings=(
                _slider("strength", "Blur strength", 60, 10, 100, 5, "%"),
                _toggle("fade_in", "Fade in", True),
            ),
        ),
        Feature(
            "menu_shader",
            "Menu Shader",
            "An animated shader background on menu screens.",
            "interface", "companion",
            settings=(
                _choice("shader", "Shader", "waves", "waves", "gradient", "particles"),
                _slider("intensity", "Intensity", 50, 10, 100, 5, "%"),
            ),
        ),

        # ==================================================================
        # UTILITY
        # ==================================================================
        Feature(
            "toggle_sprint",
            "ToggleSprint",
            "Sprint as a toggle with an on-screen state indicator.",
            "utility", "companion",
            default_enabled=True,
            settings=(
                _toggle("show_indicator", "Show HUD indicator", True),
                _text("indicator_text", "Indicator text", "[Sprinting]"),
                _toggle("keep_after_death", "Stay toggled after respawn", True),
            ),
        ),
        Feature(
            "toggle_sneak",
            "ToggleSneak",
            "Sneak as a toggle, with the same style of indicator.",
            "utility", "companion",
            settings=(
                _toggle("show_indicator", "Show HUD indicator", True),
                _text("indicator_text", "Indicator text", "[Sneaking]"),
            ),
        ),
        Feature(
            "zoom",
            "Zoom",
            "OptiFine-style zoom key with smooth interpolation.",
            "utility", "mod",
            modrinth_slug="zoomify", fallback_query="zoomify zoom",
            default_enabled=True,
            settings=(
                _slider("level", "Zoom level", 4, 2, 10, 1, "x"),
                _toggle("smooth", "Smooth zoom", True),
                _toggle("scroll_adjust", "Scroll to adjust while zoomed", True),
            ),
        ),
        Feature(
            "smooth_camera",
            "Smooth Camera",
            "Cinematic-camera smoothing on demand, not just while zoomed.",
            "utility", "companion",
            settings=(
                _slider("smoothing", "Smoothing", 50, 10, 100, 5, "%"),
                _toggle("only_zoomed", "Only while zoomed", False),
            ),
        ),
        Feature(
            "fullbright",
            "Fullbright",
            "Maximum gamma — identical to turning brightness past 100%%. "
            "Includes the full gamma slider.",
            "utility", "companion",
            settings=(
                _slider("gamma", "Gamma slider", 400, 100, 1600, 50, "%"),
                _toggle("night_vision_look", "Simulate night-vision look", False),
            ),
        ),
        Feature(
            "time_changer",
            "Time Changer",
            "Freeze the *visual* time of day on your screen — sunsets forever. "
            "The world's real time is untouched.",
            "utility", "companion",
            settings=(
                _slider("time_of_day", "Visual time (ticks)", 6000, 0, 24000, 500),
                _toggle("lock", "Lock visual time", False),
            ),
        ),
        Feature(
            "weather_visuals",
            "Weather Toggle",
            "Hide rain and snow rendering client-side. Weather still happens; "
            "you just don't have to look at it.",
            "utility", "companion",
            settings=(
                _toggle("hide_rain", "Hide rain", True),
                _toggle("hide_snow", "Hide snow", False),
                _toggle("mute_weather", "Mute weather sounds", False),
            ),
        ),
        Feature(
            "minimap",
            "Minimap & waypoints",
            "Xaero's minimap with waypoints and death markers. On competitive "
            "networks Dwine installs the Fair-Play build (no cave map, no "
            "entity radar) automatically.",
            "utility", "mod",
            modrinth_slug="xaeros-minimap", fallback_query="xaero minimap",
            flags=(FLAG_RADAR_LIKE,),
            competitive_alternative="xaeros-minimap-fair",
            settings=(
                _slider("size", "Minimap size", 100, 50, 200, 10, "%"),
                _toggle("death_waypoints", "Death waypoints", True),
            ),
        ),
        Feature(
            "skip_death_screen",
            "Skip death screen",
            "Respawn instantly without clicking through the death screen.",
            "utility", "companion",
            settings=(
                _slider("delay_ms", "Respawn after", 0, 0, 2000, 100, "ms"),
            ),
        ),
        Feature(
            "no_friend_damage",
            "Friend guard",
            "Suppresses *your own* attack input against marked friends so you "
            "never hit them by accident. Only restricts you — it cannot "
            "change what the server does.",
            "utility", "companion",
            settings=(
                _text("friends", "Friends (comma-separated names)", ""),
            ),
        ),
        Feature(
            "auto_clicker",
            "Auto clicker (singleplayer only)",
            "Holds repeated clicks for AFK-safe singleplayer tasks. Hard-"
            "disabled on every multiplayer server: input automation breaks "
            "the rules of Hypixel and most networks, so Dwine physically "
            "does not run it outside singleplayer.",
            "utility", "companion",
            flags=(FLAG_INPUT_AUTOMATION,),
            options={"cps": 8, "singleplayer_only": True},
            settings=(
                _slider("cps", "Clicks per second", 8, 1, 20, 1),
            ),
        ),
        Feature(
            "screenshot_manager",
            "Screenshot manager",
            "Gallery, editor, and quick sharing for your screenshots.",
            "utility", "launcher",
            default_enabled=True,
            settings=(
                _toggle("copy_to_clipboard", "Copy new screenshots to clipboard", False),
            ),
        ),
        Feature(
            "replay",
            "Replay system",
            "Record and re-watch sessions with the Replay Mod (Hypixel-allowed).",
            "utility", "mod",
            modrinth_slug="replaymod", fallback_query="replay mod",
            settings=(
                _toggle("auto_record", "Record every session", False),
            ),
        ),

        # ==================================================================
        # HYPIXEL
        # ==================================================================
        Feature(
            "skyblock_utilities",
            "Skyblock utilities",
            "Waypoints, dungeon map, ability timers, drop trackers and "
            "overlays via Skyblocker — built to Hypixel's mod policy.",
            "hypixel", "mod",
            modrinth_slug="skyblocker-liap", fallback_query="skyblocker",
            settings=(
                _toggle("dungeon_map", "Dungeon map", True),
                _toggle("drop_trackers", "Drop trackers", True),
            ),
        ),
        Feature(
            "bedwars_utilities",
            "Bedwars utilities",
            "Resource timers and team overlays using only visible scoreboard "
            "data. No stat advantages, no automation.",
            "hypixel", "companion",
            settings=(
                _toggle("resource_timers", "Resource upgrade timers", True),
                _toggle("team_overlay", "Team overlay", True),
            ),
        ),
        Feature(
            "level_head",
            "Level head",
            "Shows Hypixel network levels above players (public API data).",
            "hypixel", "companion",
            settings=(
                _color("color", "Level color", "#FFD166"),
            ),
        ),
        Feature(
            "nick_hider",
            "Nick hider",
            "Hides your own name/skin locally for streaming privacy.",
            "hypixel", "companion",
            settings=(
                _text("display_name", "Replacement name", "You"),
                _toggle("hide_skin", "Also hide your skin", False),
            ),
        ),
        Feature(
            "party_hud",
            "Party HUD",
            "Party member list with health from visible packets only.",
            "hypixel", "companion",
            settings=(
                _toggle("show_health", "Show health", True),
                _toggle("compact", "Compact mode", False),
            ),
        ),

        # ==================================================================
        # MEDIA
        # ==================================================================
        Feature(
            "spotify_miniplayer",
            "Spotify miniplayer",
            "Now-playing overlay with controls, powered by Spotify Connect.",
            "media", "launcher",
            settings=(
                _toggle("show_album_art", "Show album art", True),
                _slider("opacity", "Overlay opacity", 90, 30, 100, 5, "%"),
            ),
        ),
        Feature(
            "discord_rpc",
            "Discord Rich Presence",
            "Shows your version/server/profile in Discord.",
            "media", "launcher",
            default_enabled=True,
            settings=(
                _toggle("show_server", "Show the server you're on", True),
            ),
        ),
        Feature(
            "capes",
            "Dwine capes",
            "Client-side cosmetic capes, visible to you and other Dwine users.",
            "media", "companion",
            default_enabled=True,
            settings=(
                _choice("cape", "Cape", "dwine", "dwine", "galaxy", "ember", "none"),
            ),
        ),
    ]
}

CATEGORIES = ("performance", "hud", "visual", "chat", "interface",
              "utility", "hypixel", "media")


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


def feature_settings(config, feature_id: str) -> dict[str, Any]:
    """Effective settings for one feature: stored values over defaults."""
    feature = FEATURES[feature_id]
    stored = config.get(f"features.{feature_id}.settings", {}) or {}
    values: dict[str, Any] = {}
    for setting in feature.settings:
        values[setting.id] = stored.get(setting.id, setting.default)
    return values


def export_game_config(config, enabled: dict[str, bool] | None = None) -> dict[str, Any]:
    """The full feature state the companion mod reads in game.

    Pass the safety-enforced ``enabled`` map at launch time so the file
    on disk can never re-enable something the policy turned off.
    """
    enabled = enabled if enabled is not None else enabled_features(config)
    return {
        "version": 2,
        "features": {
            fid: {
                "enabled": bool(enabled.get(fid, False)),
                "settings": feature_settings(config, fid),
            }
            for fid in FEATURES
        },
    }

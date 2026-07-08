"""The expanded feature catalog: settings metadata, config export, drawpad."""

import pytest

from dwine.features import registry
from dwine.features.crosshair import Crosshair
from dwine.features.registry import SETTING_KINDS


def test_catalog_is_big_and_client_side():
    # The whole point of the client: a large built-in catalog.
    assert len(registry.FEATURES) >= 100
    for category in registry.CATEGORIES:
        assert registry.by_category(category), f"empty category: {category}"


def test_every_feature_has_settings_metadata():
    """Every feature exposes at least one tunable setting (companion/theme
    features must; mod-backed ones should)."""
    for fid, feature in registry.FEATURES.items():
        assert feature.settings, f"{fid} has no settings"
        seen = set()
        for setting in feature.settings:
            assert setting.id not in seen, f"{fid}: duplicate setting {setting.id}"
            seen.add(setting.id)
            assert setting.kind in SETTING_KINDS, (fid, setting.id)
            assert setting.label, (fid, setting.id)
            if setting.kind == "slider":
                assert setting.minimum <= setting.default <= setting.maximum, (
                    fid, setting.id)
            if setting.kind == "choice":
                assert setting.default in setting.choices, (fid, setting.id)
            if setting.kind == "color":
                assert str(setting.default).startswith("#"), (fid, setting.id)


def test_requested_features_present():
    """The headline features exist in the catalog."""
    for fid in (
        "toggle_sprint", "toggle_sneak", "keystrokes", "cps_counter",
        "fps_counter", "ping_display", "coordinates_hud", "clock_hud",
        "compass_hud", "armor_hud", "potion_hud", "direction_hud",
        "speed_hud", "stopwatch_hud", "combo_counter", "hit_delay_indicator",
        "hit_distance", "entity_hitboxes", "block_hitboxes", "block_outline",
        "chunk_borders", "light_overlay", "mob_health", "mob_nameplates",
        "arrow_trajectory", "projectile_path", "hit_color", "damage_tint",
        "block_break_overlay", "better_particles", "swing_animations",
        "old_animations", "wavey_capes", "wavey_skins", "custom_crosshair",
        "crosshair_animations", "selection_highlight", "cooldown_indicator",
        "block_overlay", "damage_particles", "block_hit_delay", "auto_gg",
        "match_timer", "custom_hud", "transparent_chat", "chat_animations",
        "chat_filter", "chat_timestamps", "chat_heads", "better_tab",
        "server_info_hud", "scoreboard_customizer", "bossbar_customizer",
        "hotbar_customizer", "inventory_blur", "inventory_animations",
        "menu_blur", "menu_shader", "zoom", "smooth_camera", "motion_blur",
        "saturation_hud", "fps_boost", "memory_cleaner", "entity_culling",
        "particle_culling", "chunk_culling", "shadow_toggle",
        "weather_visuals", "time_changer", "fullbright", "fps_graph",
        "chunk_graph", "render_distance", "entity_distance",
        "animation_toggle", "vsync_toggle", "antialiasing", "mipmap_control",
        "fog_toggle", "crosshair_movement", "custom_fonts", "custom_colors",
    ):
        assert fid in registry.FEATURES, f"missing feature: {fid}"


def test_feature_settings_merge_user_values(config):
    config.set("features.keystrokes.settings.key_color", "#123456")
    values = registry.feature_settings(config, "keystrokes")
    assert values["key_color"] == "#123456"
    assert values["show_mouse"] is True  # untouched default survives


def test_export_game_config_respects_enforced_map(config):
    config.set("features.auto_clicker.enabled", True)
    enforced = registry.enabled_features(config)
    enforced["auto_clicker"] = False  # what safety.enforce() does on servers
    payload = registry.export_game_config(config, enforced)
    assert payload["features"]["auto_clicker"]["enabled"] is False
    assert payload["features"]["keystrokes"]["settings"]["show_mouse"] is True
    assert len(payload["features"]) == len(registry.FEATURES)


def test_no_presets_anywhere():
    with pytest.raises(ImportError):
        import dwine.content.presets  # noqa: F401
    from dwine.launcher import profiles

    assert not hasattr(profiles, "BUILTIN_PRESETS")
    assert not hasattr(profiles.ProfileStore, "create_from_preset")


def test_profile_store_ensure_default():
    from dwine.launcher.profiles import ProfileStore

    store = ProfileStore()
    profile = store.ensure_default()
    assert profile.name == "Default"
    # idempotent: a second call returns the existing profile
    assert store.ensure_default().slug == profile.slug


def test_custom_crosshair_pixels_render():
    crosshair = Crosshair(
        shape="custom", size=15,
        pixels={"7,7": "#FF0000", "0,0": "#FFFFFF", "99,99": "#000000",
                "junk": "#000000"},
    )
    # out-of-range and malformed keys are dropped
    assert set(crosshair.pixels) == {"7,7", "0,0"}
    image = crosshair.render(scale=2)
    assert image.size == (30, 30)
    assert image.getpixel((14, 14)) == (255, 0, 0, 255)
    assert image.getpixel((0, 0)) == (255, 255, 255, 255)
    assert image.getpixel((29, 29)) == (0, 0, 0, 0)  # untouched = transparent

    roundtrip = Crosshair.from_dict(crosshair.to_dict())
    assert roundtrip.pixels == crosshair.pixels


def test_path_hint_regression():
    """`dwine setup-path` used to crash: a second zero-arg path_hint()
    shadowed the real one."""
    from pathlib import Path

    from dwine.core.command import path_hint, user_bin_dir

    with_arg = path_hint(Path("/somewhere/dwine"))
    without_arg = path_hint()
    assert str(user_bin_dir()) in with_arg
    assert "PATH" in without_arg

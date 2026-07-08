"""The non-negotiable tests: safety policy and catalog audit."""

from dwine.features import registry, safety


def test_catalog_audit_passes():
    assert safety.audit_catalog() == []


def test_every_feature_has_valid_metadata():
    for fid, feature in registry.FEATURES.items():
        assert feature.category in registry.CATEGORIES, fid
        assert feature.kind in ("mod", "theme", "launcher", "companion", "bundled"), fid
        assert feature.name and feature.description, fid
        if feature.kind == "mod":
            assert feature.modrinth_slug or feature.fallback_query, fid


def test_competitive_host_matching():
    assert safety.is_competitive("play.hypixel.net")
    assert safety.is_competitive("mc.hypixel.net:25565")
    assert safety.is_competitive("HYPIXEL.NET")
    assert not safety.is_competitive("myfriendsserver.example.com")
    assert not safety.is_competitive("nothypixel.example")


def test_automation_disabled_on_any_multiplayer():
    enabled = {"auto_clicker": True, "zoom": True}
    actions = safety.enforce(enabled, server="some.random-smp.example")
    assert enabled["auto_clicker"] is False
    assert enabled["zoom"] is True  # QoL features untouched
    assert any(a.feature_id == "auto_clicker" and a.action == "disabled"
               for a in actions)


def test_automation_allowed_in_singleplayer():
    enabled = {"auto_clicker": True}
    actions = safety.enforce(enabled, server=None)
    assert enabled["auto_clicker"] is True
    assert actions == []


def test_radar_swapped_on_competitive():
    enabled = {"minimap": True}
    actions = safety.enforce(enabled, server="play.hypixel.net")
    assert enabled["minimap"] is True  # still on, but…
    assert any(a.action == "fair_play_variant" for a in actions)


def test_radar_untouched_on_private_server():
    enabled = {"minimap": True}
    actions = safety.enforce(enabled, server="my-own-smp.example")
    assert actions == []

"""Offline launcher-core tests: rules, merging, command building, profiles."""

from dwine.launcher import rules
from dwine.launcher.crash import analyze_text
from dwine.launcher.install import maven_to_path, merge_version_json
from dwine.launcher.profiles import Profile, ProfileStore
from dwine.launcher.rules import substitute


def test_rules_no_rules_allows():
    assert rules.rules_allow(None)
    assert rules.rules_allow([])


def test_rules_os_gating():
    allow_all = [{"action": "allow"}]
    assert rules.rules_allow(allow_all)
    deny_current = [
        {"action": "allow"},
        {"action": "disallow", "os": {"name": rules.current_os()}},
    ]
    assert not rules.rules_allow(deny_current)
    allow_other_only = [{"action": "allow", "os": {"name": "beos"}}]
    assert not rules.rules_allow(allow_other_only)


def test_rules_feature_gating():
    demo_rule = [{"action": "allow", "features": {"is_demo_user": True}}]
    assert not rules.rules_allow(demo_rule, {"is_demo_user": False})
    assert rules.rules_allow(demo_rule, {"is_demo_user": True})


def test_substitute():
    out = substitute("--width ${resolution_width} ${unknown}", {"resolution_width": "1920"})
    assert out == "--width 1920 "


def test_maven_to_path():
    assert (
        maven_to_path("net.fabricmc:fabric-loader:0.15.11")
        == "net/fabricmc/fabric-loader/0.15.11/fabric-loader-0.15.11.jar"
    )
    assert (
        maven_to_path("org.lwjgl:lwjgl:3.3.3:natives-linux")
        == "org/lwjgl/lwjgl/3.3.3/lwjgl-3.3.3-natives-linux.jar"
    )


def test_merge_version_json():
    parent = {
        "id": "1.20.4",
        "mainClass": "net.minecraft.client.main.Main",
        "libraries": [{"name": "a:a:1"}],
        "arguments": {"game": ["--base"], "jvm": ["-Xbase"]},
    }
    child = {
        "id": "fabric-loader-0.15.11-1.20.4",
        "inheritsFrom": "1.20.4",
        "mainClass": "net.fabricmc.loader.impl.launch.knot.KnotClient",
        "libraries": [{"name": "b:b:2"}],
        "arguments": {"game": ["--extra"], "jvm": []},
    }
    merged = merge_version_json(parent, child)
    assert merged["mainClass"].endswith("KnotClient")
    assert merged["jar"] == "1.20.4"
    assert {lib["name"] for lib in merged["libraries"]} == {"a:a:1", "b:b:2"}
    assert merged["arguments"]["game"] == ["--base", "--extra"]


def test_profile_store_roundtrip():
    store = ProfileStore()
    profile = Profile(name="My PvP Setup", version="1.8.9", loader="vanilla",
                      server="play.example.com")
    store.save(profile)
    loaded = store.load("My PvP Setup")
    assert loaded.version == "1.8.9"
    assert loaded.server == "play.example.com"
    assert loaded.slug == "my-pvp-setup"
    assert store.exists("my-pvp-setup")
    store.delete("My PvP Setup")
    assert not store.exists("my-pvp-setup")


def test_profile_export_import(tmp_path):
    store = ProfileStore()
    profile = Profile(name="Exportable", version="1.21", loader="fabric")
    store.save(profile)
    (profile.game_dir / "config").mkdir(parents=True)
    (profile.game_dir / "config" / "some.json").write_text("{}")
    (profile.game_dir / "options.txt").write_text("fov:0.5")

    archive = store.export("Exportable", tmp_path / "out.zip")
    store.delete("Exportable", remove_data=True)
    imported = store.import_(archive, rename="Imported")
    assert imported.name == "Imported"
    assert (imported.game_dir / "options.txt").read_text() == "fov:0.5"
    assert (imported.game_dir / "config" / "some.json").exists()


def test_crash_analyzer_patterns():
    findings = analyze_text("java.lang.OutOfMemoryError: Java heap space")
    assert any(f.title == "Out of memory" for f in findings)

    text = ("net.fabricmc.loader.impl.FormattedException: mod 'sodium' "
            "requires any version of mod 'fabric-api', which is missing!")
    findings = analyze_text(text)
    titles = {f.title for f in findings}
    assert "Missing Fabric dependency" in titles

    assert analyze_text("everything is fine, no crash here") == []


def test_offline_session_is_deterministic():
    from dwine.launcher.auth import offline_session

    first = offline_session("Steve")
    second = offline_session("Steve")
    assert first["uuid"] == second["uuid"]
    assert first["access_token"] == "0"

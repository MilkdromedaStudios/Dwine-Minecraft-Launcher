"""Offline tests for the Dwine client-mod companion integration."""

import json

from dwine.launcher import companion
from dwine.launcher.profiles import Profile, ProfileStore


def _fabric_profile() -> Profile:
    profile = Profile(name="Client Test", version="26.2", loader="fabric")
    ProfileStore().save(profile)
    return profile


def test_catalog_names_are_unique():
    names = [feat["name"] for feat in companion.FEATURES]
    assert len(names) == len(set(names))
    assert "FPS" in names and "Zoom" in names


def test_mod_supports_version():
    assert companion.mod_supports("26.2")
    assert companion.mod_supports("26.1.2")
    assert not companion.mod_supports("1.21.1")


def test_ensure_features_seeds_and_merges():
    profile = _fabric_profile()
    path = companion.ensure_features(profile)
    data = json.loads(path.read_text())
    assert data["modules"]["FPS"]["enabled"] is True
    assert set(data["modules"]) == {f["name"] for f in companion.FEATURES}

    # A position the mod saved must survive a re-seed.
    data["modules"]["FPS"]["x"] = 42
    data["modules"]["FPS"]["enabled"] = False
    path.write_text(json.dumps(data))
    companion.ensure_features(profile)
    merged = json.loads(path.read_text())
    assert merged["modules"]["FPS"]["x"] == 42
    assert merged["modules"]["FPS"]["enabled"] is False


def test_set_feature_roundtrip():
    profile = _fabric_profile()
    canonical = companion.set_feature(profile, "cps", True)
    assert canonical == "CPS"
    states = {f["name"]: f["enabled"] for f in companion.feature_states(profile)}
    assert states["CPS"] is True

    companion.set_feature(profile, "CPS", False)
    states = {f["name"]: f["enabled"] for f in companion.feature_states(profile)}
    assert states["CPS"] is False


def test_set_feature_unknown_raises():
    profile = _fabric_profile()
    try:
        companion.set_feature(profile, "Aimbot", True)
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError for unknown feature")


def test_install_jar_replaces_old(tmp_path):
    profile = _fabric_profile()
    old = profile.mods_dir
    old.mkdir(parents=True, exist_ok=True)
    (old / "dwine-client-0.0.1.jar").write_text("old")

    jar = tmp_path / "dwine-client-0.1.0.jar"
    jar.write_text("new")
    dest = companion.install_jar(profile, jar)

    assert dest.name == "dwine-client-0.1.0.jar"
    installed = [p.name for p in profile.mods_dir.glob("dwine-client-*.jar")]
    assert installed == ["dwine-client-0.1.0.jar"]


def test_ensure_mod_uses_explicit_jar(tmp_path, config):
    jar = tmp_path / "dwine-client-0.1.0.jar"
    jar.write_text("jar")
    config.set("client.companion.jar", str(jar))
    config.set("client.companion.auto_dependencies", False)

    profile = _fabric_profile()
    dest = companion.ensure_mod(profile, download_ok=False)
    assert dest is not None and dest.exists()
    assert companion.features_file(profile).exists()


def test_ensure_mod_skips_wrong_loader(config):
    config.set("client.companion.auto_dependencies", False)
    profile = Profile(name="Vanilla", version="1.21.1", loader="vanilla")
    ProfileStore().save(profile)
    assert companion.ensure_mod(profile, download_ok=False) is None


def test_ensure_mod_skips_unsupported_version(tmp_path, config):
    jar = tmp_path / "dwine-client-0.1.0.jar"
    jar.write_text("jar")
    config.set("client.companion.jar", str(jar))
    profile = Profile(name="Old", version="1.20.1", loader="fabric")
    ProfileStore().save(profile)
    assert companion.ensure_mod(profile, download_ok=False) is None

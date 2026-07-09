from dwine.core.config import Config, DEFAULTS


def test_defaults_present(config):
    assert config.get("theme.name") == "dwine-dark"
    assert config.get("game.memory_mb") == 4096
    assert config.get("performance.auto_clean.enabled") is True


def test_set_get_roundtrip(config):
    config.set("game.memory_mb", 8192)
    assert config.get("game.memory_mb") == 8192
    config.set("auth.client_id", "abc-123")
    assert config.get("auth.client_id") == "abc-123"


def test_persistence(config):
    config.set("launcher.language", "de")
    reloaded = Config(path=config.path)
    assert reloaded.get("launcher.language") == "de"
    # unknown keys survive round trips (plugin settings)
    config.set("plugins.myplugin.color", "#123456")
    reloaded = Config(path=config.path)
    assert reloaded.get("plugins.myplugin.color") == "#123456"


def test_corrupt_file_recovers(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")
    config = Config(path=path)
    assert config.get("theme.name") == DEFAULTS["theme"]["name"]
    assert path.with_suffix(".json.bak").exists()


def test_toggle(config):
    original = config.get("launcher.show_snapshots")
    assert config.toggle("launcher.show_snapshots") == (not original)

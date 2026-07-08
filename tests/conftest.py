"""Test fixtures: every test runs against an isolated DWINE_HOME."""

import pytest


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("DWINE_HOME", str(tmp_path / "dwine-home"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    # Reset the config singleton so each test sees a fresh store.
    import dwine.core.config as config_module

    config_module._config = None
    yield tmp_path
    config_module._config = None


@pytest.fixture
def config():
    from dwine.core.config import get_config

    return get_config()

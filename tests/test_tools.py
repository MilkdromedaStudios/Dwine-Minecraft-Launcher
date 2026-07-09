"""Tools: varint protocol, cleaner, plugins, CLI parser."""

import time

from dwine.tools.ping import pack_varint, read_varint


def test_varint_roundtrip():
    for value in (0, 1, 127, 128, 255, 25565, 2**21, 2**31 - 1):
        encoded = pack_varint(value)
        pos = {"i": 0}

        def reader(n):
            chunk = encoded[pos["i"] : pos["i"] + n]
            pos["i"] += n
            return chunk

        assert read_varint(reader) == value


def test_cleaner_respects_age(tmp_path):
    from dwine.core.config import get_config
    from dwine.launcher.profiles import Profile, ProfileStore
    from dwine.tools.cleaner import clean_profile

    store = ProfileStore()
    profile = Profile(name="CleanMe", version="1.21")
    store.save(profile)
    logs = profile.game_dir / "logs"
    logs.mkdir(parents=True)
    old = logs / "old.log"
    old.write_text("x" * 1000)
    fresh = logs / "fresh.log"
    fresh.write_text("y" * 1000)
    stale_time = time.time() - 30 * 86400
    import os

    os.utime(old, (stale_time, stale_time))

    get_config().set("performance.auto_clean.max_log_age_days", 14)
    report = clean_profile(profile, dry_run=False)
    assert not old.exists()
    assert fresh.exists()
    assert report.bytes_freed == 1000


def test_plugin_loader(tmp_path):
    from dwine.core import paths
    from dwine.plugins.loader import load_all

    plugin_dir = paths.plugins_dir()
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "hello.py").write_text(
        "PLUGIN = {'id': 'hello', 'name': 'Hello', 'version': '1.0'}\n"
        "def setup(api):\n"
        "    api.register_command('greet', lambda: 'hi')\n"
    )
    (plugin_dir / "broken.py").write_text("raise RuntimeError('boom')\n")

    plugins = {p.id: p for p in load_all()}
    assert plugins["hello"].ok
    assert "greet" in plugins["hello"].api.commands
    assert not plugins["broken"].ok  # broken plugin doesn't kill the loader


def test_cli_parser_smoke():
    from dwine.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["launch", "fps-mode", "--server", "example.com"])
    assert args.command == "launch"
    assert args.server == "example.com"
    args = parser.parse_args(["mods", "install", "sodium", "--profile", "fps"])
    assert args.action == "install" and args.query == "sodium"


def test_setup_path_writes_user_command(tmp_path, monkeypatch):
    from dwine.core import command

    monkeypatch.setenv("DWINE_BIN_DIR", str(tmp_path / "bin"))
    target = command.install_command()
    assert target.exists()
    assert "python" in target.read_text(encoding="utf-8").lower()
    assert "-m dwine" in target.read_text(encoding="utf-8")
    hint = command.path_hint(target)
    assert f"Command file location: {target}" in hint
    assert "Environment variable to edit: PATH" in hint
    assert str(target.parent) in hint


def test_update_parser_and_install_target():
    from dwine.cli import build_parser
    from dwine.launcher.update import UpdateInfo

    parser = build_parser()
    args = parser.parse_args(["update", "--check"])
    assert args.command == "update"
    assert args.check is True
    info = UpdateInfo(current="0.1.0", latest="v0.2.0", url="", notes="")
    assert info.available
    assert info.install_target.endswith("@v0.2.0")

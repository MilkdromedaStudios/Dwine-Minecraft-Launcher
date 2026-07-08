"""The ``dwine`` command line — everything the UI does, headless.

Run ``dwine`` with no arguments to open the launcher UI; every subcommand
below works over SSH, in scripts, and on servers without a display.
"""

from __future__ import annotations

import argparse
import sys

from . import __app_name__, __version__
from .core import paths
from .core.config import get_config
from .core.events import bus
from .core.log import setup as setup_logging


def _progress_printer(event: str, payload: dict) -> None:
    if event == "install.step":
        step = payload.get("step", "")
        detail = payload.get("detail", "")
        print(f"  [{step}] {detail}".rstrip())


# --------------------------------------------------------------------------
# subcommand handlers
# --------------------------------------------------------------------------

def cmd_ui(_args) -> int:
    from . import ui

    return ui.run()


def cmd_versions(args) -> int:
    from .launcher import manifest

    versions = manifest.list_versions(
        releases=True, snapshots=args.snapshots, old_versions=args.old
    )
    for version in versions[: args.limit]:
        print(f"{version.id:<16} {version.type:<10} {version.release_time[:10]}")
    return 0


def cmd_install(args) -> int:
    from .launcher.install import install_version
    from .launcher.loaders import ensure_loader

    bus.on("install.step", _progress_printer)
    version_id = ensure_loader(args.loader, args.version, args.loader_version)
    install_version(version_id)
    print(f"Installed: {version_id}")
    return 0


def cmd_login(_args) -> int:
    from .launcher import auth
    from .launcher.accounts import AccountStore

    def show_code(url: str, code: str) -> None:
        print(f"\nOpen {url} and enter code: {code}\n")

    session_obj = auth.start_device_login(show_code)
    AccountStore().add(session_obj.as_account())
    print(f"Signed in as {session_obj.name}")
    return 0


def cmd_launch(args) -> int:
    from .launcher import auth
    from .launcher.accounts import AccountStore
    from .launcher.play import launch_profile
    from .launcher.profiles import Profile, ProfileStore

    store = ProfileStore()
    if store.exists(args.profile):
        profile = store.load(args.profile)
    else:
        profile = Profile(name=args.profile, version=args.mc or "",
                          loader=args.loader)
        store.save(profile)

    if args.offline:
        account = auth.offline_session(args.offline)
        if args.server:
            print("error: offline sessions are for local testing only; "
                  "sign in with `dwine login` to join servers.")
            return 2
    else:
        account = AccountStore().active()
        if account is None:
            print("No account. Run `dwine login` first "
                  "(or use --offline NAME for singleplayer testing).")
            return 2

    bus.on("install.step", _progress_printer)
    bus.on("game.log", lambda _e, p: print(p.get("line", "")))
    exit_code = {"value": 0}
    bus.on("game.exited", lambda _e, p: exit_code.update(value=p.get("code", 0)))
    proc = launch_profile(profile, account, server=args.server)
    proc.wait()
    return int(exit_code["value"] or 0)


def cmd_profile(args) -> int:
    from .launcher.profiles import BUILTIN_PRESETS, Profile, ProfileStore

    store = ProfileStore()
    if args.action == "list":
        for profile in store.list():
            print(f"{profile.name:<20} {profile.version or 'latest':<10} "
                  f"{profile.loader:<8} {profile.description}")
    elif args.action == "create":
        if args.preset:
            profile = store.create_from_preset(
                args.preset, version=args.mc or "", name=args.name or "")
        else:
            profile = Profile(name=args.name or "New Profile",
                              version=args.mc or "", loader=args.loader)
            store.save(profile)
        print(f"Created profile: {profile.name}")
    elif args.action == "delete":
        store.delete(args.name, remove_data=args.purge)
        print(f"Deleted profile: {args.name}")
    elif args.action == "export":
        from pathlib import Path

        dest = store.export(args.name, Path(args.file or f"{args.name}.dwine.zip"))
        print(f"Exported → {dest}")
    elif args.action == "import":
        from pathlib import Path

        profile = store.import_(Path(args.file))
        print(f"Imported profile: {profile.name}")
    elif args.action == "presets":
        for key, spec in BUILTIN_PRESETS.items():
            print(f"{key:<12} {spec['display_name']:<16} {spec['description']}")
    return 0


def cmd_mods(args) -> int:
    from .content import modrinth
    from .content.mods import ModManager
    from .content.presets import PRESETS, install_preset
    from .launcher.profiles import ProfileStore

    store = ProfileStore()
    profile = store.load(args.profile)
    manager = ModManager(profile)

    if args.action == "search":
        for hit in modrinth.search(args.query or "", game_version=profile.version,
                                   loader=profile.loader):
            print(f"{hit.slug:<28} {hit.downloads:>12,}  {hit.title}")
    elif args.action == "install":
        installed = manager.install(args.query)
        print(f"Installed: {', '.join(installed)}")
    elif args.action == "remove":
        ok = manager.remove(args.query)
        print("Removed." if ok else f"{args.query} was not installed.")
    elif args.action == "list":
        for slug, entry in manager.installed().items():
            print(f"{slug:<28} {entry['version']:<16} {entry['file']}")
    elif args.action == "update":
        changed = manager.update_all()
        if changed:
            for slug, version in changed.items():
                print(f"updated {slug} → {version}")
        else:
            print("Everything is up to date.")
    elif args.action == "preset":
        if args.query not in PRESETS:
            print(f"Presets: {', '.join(PRESETS)}")
            return 2
        report = install_preset(profile, args.query)
        print(f"Installed {len(report['installed'])} mod(s); "
              f"skipped {len(report['skipped'])}: {', '.join(report['skipped'])}")
    return 0


def cmd_theme(args) -> int:
    from .theme.themes import list_themes, load_theme

    cfg = get_config()
    if args.action == "list":
        active = cfg.get("theme.name")
        for name in list_themes():
            theme = load_theme(name)
            marker = "●" if name == active else " "
            print(f"{marker} {name:<14} {theme.display_name:<14} "
                  f"{theme.get('description', '')}")
    elif args.action == "set":
        cfg.set("theme.name", args.name)
        print(f"Theme set to {args.name}")
    elif args.action == "build":
        from pathlib import Path

        from .theme.mcpack import build_pack

        theme = load_theme(args.name or cfg.get("theme.name"))
        dest = build_pack(theme, args.mc or "1.21", Path(args.out or "."))
        print(f"Resource pack written → {dest}")
    return 0


def cmd_ping(args) -> int:
    from .tools.ping import ping

    result = ping(args.host, timeout=args.timeout)
    print(f"{result.host}:{result.port}")
    print(f"  latency : {result.latency_ms} ms")
    print(f"  version : {result.version} (protocol {result.protocol})")
    print(f"  players : {result.players_online}/{result.players_max}")
    print(f"  motd    : {result.motd}")
    return 0


def cmd_clean(args) -> int:
    from .launcher.profiles import ProfileStore
    from .tools.cleaner import clean_all, human_size

    report = clean_all(ProfileStore().list(), dry_run=not args.apply)
    mode = "Freed" if args.apply else "Would free"
    print(f"{mode} {human_size(report.bytes_freed)} across "
          f"{len(report.files)} file(s)")
    if not args.apply and report.files:
        print("Run again with --apply to delete.")
    return 0


def cmd_crash(args) -> int:
    from .launcher.crash import analyze_file, latest_crash_report
    from .launcher.profiles import ProfileStore

    profile = ProfileStore().load(args.profile)
    report = latest_crash_report(profile.game_dir)
    if report is None:
        print("No crash reports found.")
        return 0
    print(f"Analyzing {report.name}:")
    findings = analyze_file(report)
    if not findings:
        print("  no known pattern matched.")
    for finding in findings:
        print(f"\n  [{finding.title}]")
        print(f"  → {finding.advice}")
    return 0


def cmd_news(_args) -> int:
    from .launcher.news import fetch_news

    for item in fetch_news():
        print(f"— {item.title} ({item.date})\n  {item.body}\n")
    return 0


def cmd_sync(args) -> int:
    from .integrations import cloudsync

    if args.action == "push":
        print(f"Snapshot → {cloudsync.push()}")
    else:
        ok = cloudsync.pull()
        print("Restored latest snapshot." if ok else "No snapshot found.")
    return 0


def cmd_safety(_args) -> int:
    from .features.safety import COMPETITIVE_NETWORKS, audit_catalog

    problems = audit_catalog()
    print("Feature catalog audit:", "PASS ✓" if not problems else "FAIL ✗")
    for problem in problems:
        print(f"  - {problem}")
    print(f"\nCompetitive networks with enforced fair-play policy "
          f"({len(COMPETITIVE_NETWORKS)}):")
    for network in COMPETITIVE_NETWORKS:
        print(f"  - {network}")
    return 1 if problems else 0


def cmd_plugins(_args) -> int:
    from .plugins.loader import load_all

    plugins = load_all()
    if not plugins:
        print(f"No plugins in {paths.plugins_dir()}")
    for plugin in plugins:
        status = "ok" if plugin.ok else f"ERROR: {plugin.error}"
        print(f"{plugin.name:<24} v{plugin.version:<8} {status}")
    return 0


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dwine",
        description=f"{__app_name__} — the fully legitimate Minecraft "
        "client + launcher.",
    )
    parser.add_argument("--version", action="version",
                        version=f"{__app_name__} {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("ui", help="open the launcher UI (default)")

    p = sub.add_parser("versions", help="list Minecraft versions")
    p.add_argument("--snapshots", action="store_true")
    p.add_argument("--old", action="store_true")
    p.add_argument("--limit", type=int, default=30)

    p = sub.add_parser("install", help="install a Minecraft version")
    p.add_argument("version")
    p.add_argument("--loader", default="vanilla",
                   choices=["vanilla", "fabric", "quilt", "forge"])
    p.add_argument("--loader-version", default="")

    sub.add_parser("login", help="add a Microsoft account (device code)")

    p = sub.add_parser("launch", help="launch a profile")
    p.add_argument("profile")
    p.add_argument("--server", default=None, help="quick-join address")
    p.add_argument("--mc", default="", help="Minecraft version for new profiles")
    p.add_argument("--loader", default="vanilla")
    p.add_argument("--offline", default="", metavar="NAME",
                   help="offline session for singleplayer testing")

    p = sub.add_parser("profile", help="manage profiles")
    p.add_argument("action", choices=["list", "create", "delete", "export",
                                      "import", "presets"])
    p.add_argument("name", nargs="?", default="")
    p.add_argument("--preset", default="", help="fps | pvp | skyblock | cinematic")
    p.add_argument("--mc", default="")
    p.add_argument("--loader", default="fabric")
    p.add_argument("--file", default="")
    p.add_argument("--purge", action="store_true",
                   help="also delete the game directory")

    p = sub.add_parser("mods", help="manage mods for a profile")
    p.add_argument("action", choices=["search", "install", "remove", "list",
                                      "update", "preset"])
    p.add_argument("query", nargs="?", default="")
    p.add_argument("--profile", required=True)

    p = sub.add_parser("theme", help="themes and the in-game pack")
    p.add_argument("action", choices=["list", "set", "build"])
    p.add_argument("name", nargs="?", default="")
    p.add_argument("--mc", default="1.21")
    p.add_argument("--out", default="")

    p = sub.add_parser("ping", help="ping a Minecraft server")
    p.add_argument("host")
    p.add_argument("--timeout", type=float, default=5.0)

    p = sub.add_parser("clean", help="clean logs, crash reports and caches")
    p.add_argument("--apply", action="store_true", help="actually delete")

    p = sub.add_parser("crash", help="analyze the latest crash report")
    p.add_argument("profile")

    sub.add_parser("news", help="show the news feed")

    p = sub.add_parser("sync", help="settings sync snapshots")
    p.add_argument("action", choices=["push", "pull"])

    sub.add_parser("safety", help="audit the feature catalog + policy")
    sub.add_parser("plugins", help="list installed plugins")
    return parser


HANDLERS = {
    "ui": cmd_ui,
    "versions": cmd_versions,
    "install": cmd_install,
    "login": cmd_login,
    "launch": cmd_launch,
    "profile": cmd_profile,
    "mods": cmd_mods,
    "theme": cmd_theme,
    "ping": cmd_ping,
    "clean": cmd_clean,
    "crash": cmd_crash,
    "news": cmd_news,
    "sync": cmd_sync,
    "safety": cmd_safety,
    "plugins": cmd_plugins,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging(verbose=getattr(args, "verbose", False))
    paths.ensure_tree()
    command = args.command or "ui"
    try:
        return HANDLERS[command](args)
    except KeyboardInterrupt:
        print("\ninterrupted")
        return 130
    except Exception as exc:  # noqa: BLE001 - single friendly error surface
        if getattr(args, "verbose", False):
            raise
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

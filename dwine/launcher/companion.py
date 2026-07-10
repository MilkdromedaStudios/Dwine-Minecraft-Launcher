"""The Dwine client mod — install it into a profile and drive its features.

The sleek in-game UI and the client modules themselves live in the Fabric mod
under ``mod/`` (built by GitHub Actions). The launcher stays in Python: on Play
it drops the built jar into a Fabric/Quilt profile's ``mods`` folder and writes
the shared ``config/dwine/features.json`` that the mod reads, so the game
starts *with* the Dwine client already configured.

Nothing here is a cheat: every feature is a client-side, server-legal visual or
quality-of-life module, exactly as in the mod.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .. import __version__
from ..core import paths
from ..core.config import get_config
from ..core.events import bus
from ..core.http import download, get_json
from .profiles import Profile

# Loaders the Fabric client mod can be dropped into (Quilt loads Fabric mods).
MOD_LOADERS = {"fabric", "quilt"}

# The Minecraft version the current mod build targets. Auto-install is limited
# to matching profiles so the game never fails to boot on an unmet dependency.
MOD_MC_TARGET = "1.21.1"

JAR_PREFIX = "dwine-client-"
RELEASES_API = "https://api.github.com/repos/MilkdromedaStudios/Dwine/releases/latest"

# Mirror of the mod's module catalogue (com.dwine.module.ModuleManager). Names
# match the mod's Module#getName exactly so the launcher and mod agree on keys.
FEATURES: list[dict[str, Any]] = [
    # HUD
    {"name": "Watermark", "category": "HUD", "enabled": True, "description": "Show the Dwine wordmark."},
    {"name": "Active List", "category": "HUD", "enabled": False, "description": "List active modules in the corner."},
    {"name": "FPS", "category": "HUD", "enabled": True, "description": "Show the current framerate."},
    {"name": "CPS", "category": "HUD", "enabled": False, "description": "Show clicks per second."},
    {"name": "Coordinates", "category": "HUD", "enabled": False, "description": "Show your XYZ position."},
    {"name": "Direction", "category": "HUD", "enabled": False, "description": "Show the direction you are facing."},
    {"name": "Ping", "category": "HUD", "enabled": False, "description": "Show your latency to the server."},
    {"name": "Clock", "category": "HUD", "enabled": False, "description": "Show the real-world time."},
    {"name": "Keystrokes", "category": "HUD", "enabled": False, "description": "Show WASD, mouse and jump keys."},
    {"name": "Armor", "category": "HUD", "enabled": False, "description": "Show equipped armour and durability."},
    {"name": "Potions", "category": "HUD", "enabled": False, "description": "Show active status effects."},
    {"name": "Session", "category": "HUD", "enabled": False, "description": "Show how long this session has run."},
    {"name": "Speed", "category": "HUD", "enabled": False, "description": "Show your horizontal speed."},
    {"name": "Biome", "category": "HUD", "enabled": False, "description": "Show your current biome."},
    # Render
    {"name": "Fullbright", "category": "Render", "enabled": False, "description": "Brighten the world to the max."},
    {"name": "Zoom", "category": "Render", "enabled": True, "description": "Hold a key to zoom in."},
    {"name": "No Bobbing", "category": "Render", "enabled": False, "description": "Disable view-bobbing sway."},
    {"name": "FOV Changer", "category": "Render", "enabled": False, "description": "Override your field of view."},
    # Movement
    {"name": "Toggle Sprint", "category": "Movement", "enabled": False, "description": "Keep sprinting hands-free."},
    {"name": "Toggle Sneak", "category": "Movement", "enabled": False, "description": "Stay sneaking hands-free."},
    {"name": "Auto Sprint", "category": "Movement", "enabled": False, "description": "Sprint when moving forward."},
    # Misc
    {"name": "Frame Limit", "category": "Misc", "enabled": False, "description": "Cap your framerate to save power."},
]


def mod_supports(version: str) -> bool:
    """True if the current mod build targets this Minecraft version."""
    return version.startswith("1.21")


# -- shared features.json ---------------------------------------------------


def features_file(profile: Profile) -> Path:
    return profile.game_dir / "config" / "dwine" / "features.json"


def default_features() -> dict[str, Any]:
    modules = {
        feat["name"]: {
            "category": feat["category"],
            "enabled": feat["enabled"],
            "description": feat["description"],
        }
        for feat in FEATURES
    }
    return {
        "schemaVersion": 1,
        "generatedBy": f"Dwine launcher {__version__}",
        "modules": modules,
    }


def load_features(profile: Profile) -> dict[str, Any]:
    path = features_file(profile)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return default_features()


def save_features(profile: Profile, data: dict[str, Any]) -> Path:
    path = features_file(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def ensure_features(profile: Profile) -> Path:
    """Merge the catalogue into the profile's features.json.

    Existing per-module state — enabled flags the user set, plus positions and
    settings the mod saved — is preserved; only missing entries are seeded.
    """
    data = load_features(profile)
    data.setdefault("schemaVersion", 1)
    modules = data.setdefault("modules", {})
    for feat in FEATURES:
        entry = modules.setdefault(feat["name"], {})
        entry.setdefault("enabled", feat["enabled"])
        entry.setdefault("description", feat["description"])
        entry["category"] = feat["category"]
    return save_features(profile, data)


def _catalog_name(name: str) -> str | None:
    for feat in FEATURES:
        if feat["name"].lower() == name.lower():
            return feat["name"]
    return None


def set_feature(profile: Profile, name: str, enabled: bool) -> str:
    """Enable/disable a feature by (case-insensitive) name. Returns canonical name."""
    canonical = _catalog_name(name)
    if canonical is None:
        raise KeyError(f"unknown feature: {name!r}")
    data = load_features(profile)
    modules = data.setdefault("modules", {})
    entry = modules.setdefault(canonical, {})
    entry["enabled"] = enabled
    entry.setdefault("category", next(f["category"] for f in FEATURES if f["name"] == canonical))
    save_features(profile, data)
    return canonical


def feature_states(profile: Profile) -> list[dict[str, Any]]:
    """The catalogue merged with the profile's current enabled state."""
    modules = load_features(profile).get("modules", {})
    out = []
    for feat in FEATURES:
        entry = modules.get(feat["name"], {})
        out.append({
            "name": feat["name"],
            "category": feat["category"],
            "description": feat["description"],
            "enabled": bool(entry.get("enabled", feat["enabled"])),
        })
    return out


# -- the mod jar ------------------------------------------------------------


def cache_dir() -> Path:
    return paths.data_dir() / "meta" / "dwine-mod"


def _jars_in(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        j for j in directory.glob(f"{JAR_PREFIX}*.jar") if not j.name.endswith("-sources.jar")
    )


def _repo_built_jar() -> Path | None:
    """A locally-built jar (mod/build/libs) — handy during development."""
    root = Path(__file__).resolve().parents[2]
    jars = _jars_in(root / "mod" / "build" / "libs")
    return jars[-1] if jars else None


def _cached_jar() -> Path | None:
    jars = _jars_in(cache_dir())
    return jars[-1] if jars else None


def _download_release_jar() -> Path | None:
    """Fetch the mod jar from the latest GitHub release, if one exists."""
    try:
        release = get_json(RELEASES_API)
    except Exception as exc:  # noqa: BLE001 - offline / no release yet
        bus.emit("companion.error", {"stage": "release", "error": str(exc)})
        return None
    for asset in release.get("assets", []):
        name = asset.get("name", "")
        if name.startswith(JAR_PREFIX) and name.endswith(".jar") and not name.endswith("-sources.jar"):
            dest = cache_dir() / name
            download(asset["browser_download_url"], dest)
            return dest
    return None


def resolve_jar(download_ok: bool = True) -> Path | None:
    """Find the Dwine mod jar: explicit path → dev build → cache → release."""
    cfg = get_config()
    explicit = cfg.get("client.companion.jar", "")
    if explicit and Path(explicit).exists():
        return Path(explicit)
    for finder in (_repo_built_jar, _cached_jar):
        jar = finder()
        if jar:
            return jar
    if download_ok and cfg.get("client.companion.download", True):
        return _download_release_jar()
    return None


def install_jar(profile: Profile, jar: Path) -> Path:
    """Copy the jar into the profile's mods folder, replacing older copies."""
    profile.mods_dir.mkdir(parents=True, exist_ok=True)
    for old in _jars_in(profile.mods_dir):
        old.unlink(missing_ok=True)
    dest = profile.mods_dir / jar.name
    shutil.copy2(jar, dest)
    bus.emit("companion.installed", {"profile": profile.name, "jar": dest.name})
    return dest


def ensure_dependencies(profile: Profile) -> None:
    """Install Fabric API (or Quilt's QSL) so the client mod can load."""
    from ..content.mods import ModManager

    slug = "fabric-api" if profile.loader == "fabric" else "qsl"
    try:
        ModManager(profile).install(slug)
    except Exception as exc:  # noqa: BLE001 - best effort, never blocks Play
        bus.emit("companion.error", {"stage": "dependency", "slug": slug, "error": str(exc)})


def ensure_mod(profile: Profile, download_ok: bool = True) -> Path | None:
    """Make sure the Dwine client mod is present in a Fabric/Quilt profile.

    Returns the installed jar path, or ``None`` when it does not apply (wrong
    loader / unsupported version) or no jar could be found.
    """
    if profile.loader not in MOD_LOADERS:
        return None
    if not mod_supports(profile.effective_version()):
        bus.emit("companion.skipped", {
            "profile": profile.name,
            "reason": f"Dwine client targets Minecraft {MOD_MC_TARGET}; "
                      f"profile is {profile.effective_version()}",
        })
        return None
    jar = resolve_jar(download_ok=download_ok)
    if jar is None:
        bus.emit("companion.skipped", {
            "profile": profile.name,
            "reason": "no Dwine mod jar found (build mod/ or publish a release)",
        })
        return None
    ensure_features(profile)
    if get_config().get("client.companion.auto_dependencies", True):
        ensure_dependencies(profile)
    return install_jar(profile, jar)


def status(profile: Profile) -> dict[str, Any]:
    installed = _jars_in(profile.mods_dir)
    return {
        "loader": profile.loader,
        "applies": profile.loader in MOD_LOADERS,
        "version": profile.effective_version(),
        "version_supported": mod_supports(profile.effective_version()),
        "jar_source": str(resolve_jar(download_ok=False) or ""),
        "installed": [j.name for j in installed],
        "features_file": str(features_file(profile)),
    }

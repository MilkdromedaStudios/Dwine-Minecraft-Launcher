"""Discovers and loads plugins from the plugins directory."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path

from ..core import paths
from ..core.log import get
from .api import DwineAPI

log = get("plugins")


@dataclass
class LoadedPlugin:
    id: str
    name: str
    version: str
    path: Path
    api: DwineAPI
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error


def discover() -> list[Path]:
    folder = paths.plugins_dir()
    if not folder.exists():
        return []
    return sorted(
        p for p in folder.glob("*.py") if not p.name.startswith("_")
    )


def load_plugin(path: Path) -> LoadedPlugin:
    plugin_id = path.stem
    api = DwineAPI(plugin_id=plugin_id)
    try:
        spec = importlib.util.spec_from_file_location(f"dwine_plugin_{plugin_id}", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load spec for {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        meta = getattr(module, "PLUGIN", {})
        setup = getattr(module, "setup", None)
        if not callable(setup):
            raise AttributeError("plugin has no setup(api) function")
        setup(api)
        return LoadedPlugin(
            id=meta.get("id", plugin_id),
            name=meta.get("name", plugin_id),
            version=meta.get("version", "0.0"),
            path=path,
            api=api,
        )
    except Exception as exc:  # noqa: BLE001 - a broken plugin must not kill Dwine
        log.warning("plugin %s failed to load: %s", plugin_id, exc)
        return LoadedPlugin(
            id=plugin_id, name=plugin_id, version="?", path=path, api=api,
            error=str(exc),
        )


def load_all() -> list[LoadedPlugin]:
    return [load_plugin(path) for path in discover()]

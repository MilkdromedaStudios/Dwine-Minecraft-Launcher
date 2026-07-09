"""Dwine's JSON settings system.

A single ``settings.json`` holds every user-tunable option, addressed with
dot-paths (``config.get("theme.name")``).  Writes are atomic, defaults are
deep-merged, and unknown keys survive round-trips so plugins can store
their own settings safely.
"""

from __future__ import annotations

import copy
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable

from . import paths

DEFAULTS: dict[str, Any] = {
    "meta": {"settings_version": 1},
    "theme": {
        "name": "dwine-dark",
        "background": {"image": "", "animated": True, "blur": 12},
        "accent": "",  # empty = use theme accent
    },
    "launcher": {
        "keep_open_while_playing": True,
        "show_snapshots": False,
        "show_old_versions": False,
        "concurrent_downloads": 8,
        "language": "en",
        "auto_update": True,
        "close_to_tray": False,
    },
    "game": {
        "memory_mb": 4096,
        "jvm_args": [],
        "fullscreen": False,
        "width": 1280,
        "height": 720,
        "java_path": "",  # empty = auto-discover / managed runtime
    },
    "performance": {
        "auto_clean": {"enabled": True, "max_log_age_days": 14, "max_cache_mb": 2048},
    },
    "auth": {
        "client_id": "",  # optional custom Azure app for Microsoft login
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


class Config:
    """Thread-safe dot-path settings store backed by one JSON file."""

    def __init__(self, path: Path | None = None):
        self.path = path or paths.config_file()
        self._lock = threading.RLock()
        self._listeners: list[Callable[[str, Any], None]] = []
        self._data: dict[str, Any] = {}
        self.reload()

    # -- persistence -------------------------------------------------

    def reload(self) -> None:
        with self._lock:
            stored: dict[str, Any] = {}
            if self.path.exists():
                try:
                    stored = json.loads(self.path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    # Corrupt settings: keep a backup, fall back to defaults.
                    backup = self.path.with_suffix(".json.bak")
                    try:
                        self.path.replace(backup)
                    except OSError:
                        pass
            self._data = _deep_merge(DEFAULTS, stored)

    def save(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(self._data, fh, indent=2, sort_keys=True)
                os.replace(tmp, self.path)
            except BaseException:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise

    # -- access ------------------------------------------------------

    def get(self, dotted: str, default: Any = None) -> Any:
        with self._lock:
            node: Any = self._data
            for part in dotted.split("."):
                if not isinstance(node, dict) or part not in node:
                    return default
                node = node[part]
            return copy.deepcopy(node)

    def set(self, dotted: str, value: Any, save: bool = True) -> None:
        with self._lock:
            parts = dotted.split(".")
            node = self._data
            for part in parts[:-1]:
                node = node.setdefault(part, {})
                if not isinstance(node, dict):
                    raise TypeError(f"cannot set {dotted!r}: {part!r} is not an object")
            node[parts[-1]] = value
            if save:
                self.save()
        for listener in list(self._listeners):
            listener(dotted, value)

    def toggle(self, dotted: str, save: bool = True) -> bool:
        new = not bool(self.get(dotted, False))
        self.set(dotted, new, save=save)
        return new

    def as_dict(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._data)

    def on_change(self, listener: Callable[[str, Any], None]) -> None:
        self._listeners.append(listener)


_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config

"""The stable surface plugins are allowed to touch.

A plugin is a Python file in the Dwine plugins directory exposing::

    PLUGIN = {"id": "my-plugin", "name": "My Plugin", "version": "1.0"}

    def setup(api: DwineAPI) -> None:
        api.on("game.started", lambda event, data: ...)

Plugins extend the launcher — commands, event hooks, UI pages, extra
content sources. They cannot inject code into the game process, which
keeps the no-cheat guarantee intact no matter what plugins you install.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..core.config import Config, get_config
from ..core.events import bus
from ..launcher.profiles import ProfileStore


@dataclass
class DwineAPI:
    plugin_id: str
    ui_pages: list[tuple[str, Callable]] = field(default_factory=list)
    commands: dict[str, Callable] = field(default_factory=dict)

    # -- events ----------------------------------------------------------

    def on(self, event: str, handler: Callable[[str, dict], None]) -> Callable[[], None]:
        """Subscribe to launcher events (see dwine.core.events for names)."""
        return bus.on(event, handler)

    def emit(self, event: str, payload: dict | None = None) -> None:
        bus.emit(f"plugin.{self.plugin_id}.{event}", payload or {})

    # -- config ------------------------------------------------------------

    @property
    def config(self) -> Config:
        return get_config()

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.config.get(f"plugins.{self.plugin_id}.{key}", default)

    def set_setting(self, key: str, value: Any) -> None:
        self.config.set(f"plugins.{self.plugin_id}.{key}", value)

    # -- launcher objects ---------------------------------------------------

    @property
    def profiles(self) -> ProfileStore:
        return ProfileStore()

    def mod_manager(self, profile_name: str):
        from ..content.mods import ModManager

        return ModManager(self.profiles.load(profile_name))

    # -- extension points ------------------------------------------------

    def register_command(self, name: str, handler: Callable[..., Any]) -> None:
        """Add a `dwine plugin <plugin-id> <name>` CLI command."""
        self.commands[name] = handler

    def register_ui_page(self, title: str, factory: Callable) -> None:
        """Add a sidebar page to the launcher UI. ``factory(parent) -> QWidget``."""
        self.ui_pages.append((title, factory))

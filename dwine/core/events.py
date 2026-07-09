"""Tiny synchronous event bus.

Used by the launcher core to report progress, by the UI to react to it,
and by plugins to hook into Dwine without touching internals.

Well-known events:
    download.progress   {"url", "done", "total"}
    install.step        {"version", "step", "detail"}
    game.launching      {"profile", "command"}
    game.started        {"profile", "pid"}
    game.exited         {"profile", "code"}
    game.log            {"profile", "line"}
    mods.installed      {"slug", "version", "file"}
    theme.changed       {"name"}
"""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any, Callable

Handler = Callable[[str, dict[str, Any]], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._lock = threading.RLock()

    def on(self, event: str, handler: Handler) -> Callable[[], None]:
        """Subscribe. ``event`` may end with ``*`` as a prefix wildcard.

        Returns an unsubscribe callable.
        """
        with self._lock:
            self._handlers[event].append(handler)

        def off() -> None:
            with self._lock:
                try:
                    self._handlers[event].remove(handler)
                except ValueError:
                    pass

        return off

    def emit(self, event: str, payload: dict[str, Any] | None = None) -> None:
        payload = payload or {}
        with self._lock:
            targets: list[Handler] = []
            for pattern, handlers in self._handlers.items():
                if pattern == event or (
                    pattern.endswith("*") and event.startswith(pattern[:-1])
                ):
                    targets.extend(handlers)
        for handler in targets:
            try:
                handler(event, payload)
            except Exception:  # noqa: BLE001 - one bad listener must not break the bus
                import logging

                logging.getLogger("dwine.events").exception(
                    "event handler failed for %s", event
                )


bus = EventBus()

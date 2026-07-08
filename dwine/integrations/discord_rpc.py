"""Discord Rich Presence.

Uses ``pypresence`` when installed (``pip install dwine[full]``) and
degrades to a silent no-op otherwise, so the launcher never hard-depends
on Discord being present.
"""

from __future__ import annotations

import time

from ..core.events import bus
from ..core.log import get

log = get("discord")
CLIENT_ID = "1290000000000000000"  # Dwine's Discord application id


class RichPresence:
    def __init__(self) -> None:
        self._rpc = None
        self._start = time.time()

    def connect(self) -> bool:
        try:
            from pypresence import Presence
        except ImportError:
            log.debug("pypresence not installed; rich presence disabled")
            return False
        try:
            self._rpc = Presence(CLIENT_ID)
            self._rpc.connect()
        except Exception as exc:  # Discord not running, socket busy, ...
            log.debug("discord unavailable: %s", exc)
            self._rpc = None
            return False
        self._wire_events()
        self.set_state("In the launcher")
        return True

    def _wire_events(self) -> None:
        bus.on("game.started", lambda _e, p: self.set_state(
            f"Playing {p.get('profile', 'Minecraft')}"))
        bus.on("game.exited", lambda _e, _p: self.set_state("In the launcher"))

    def set_state(self, state: str, details: str = "Dwine Client") -> None:
        if not self._rpc:
            return
        try:
            self._rpc.update(
                state=state,
                details=details,
                start=int(self._start),
                large_image="dwine",
                large_text="Dwine — the legit client",
            )
        except Exception as exc:
            log.debug("rpc update failed: %s", exc)

    def close(self) -> None:
        if self._rpc:
            try:
                self._rpc.close()
            except Exception:
                pass
            self._rpc = None

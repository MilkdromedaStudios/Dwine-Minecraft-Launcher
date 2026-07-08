"""Account manager: stores Microsoft accounts, refreshes tokens on demand."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ..core import paths
from . import auth


class AccountStore:
    def __init__(self, path: Path | None = None):
        self.path = path or paths.accounts_file()
        self._data: dict[str, Any] = {"active": None, "accounts": {}}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        try:  # tokens are sensitive: owner-only on POSIX
            self.path.chmod(0o600)
        except OSError:
            pass

    # ------------------------------------------------------------------

    def add(self, account: dict[str, Any], make_active: bool = True) -> None:
        self._data["accounts"][account["uuid"]] = account
        if make_active or not self._data.get("active"):
            self._data["active"] = account["uuid"]
        self._save()

    def remove(self, uuid: str) -> None:
        self._data["accounts"].pop(uuid, None)
        if self._data.get("active") == uuid:
            remaining = list(self._data["accounts"])
            self._data["active"] = remaining[0] if remaining else None
        self._save()

    def list(self) -> list[dict[str, Any]]:
        return list(self._data["accounts"].values())

    def set_active(self, uuid: str) -> None:
        if uuid not in self._data["accounts"]:
            raise KeyError(uuid)
        self._data["active"] = uuid
        self._save()

    def active(self, refresh_if_needed: bool = True) -> dict[str, Any] | None:
        uuid = self._data.get("active")
        if not uuid or uuid not in self._data["accounts"]:
            return None
        account = self._data["accounts"][uuid]
        if (
            refresh_if_needed
            and account.get("user_type") == "msa"
            and account.get("refresh_token")
            and time.time() >= float(account.get("expires_at", 0))
        ):
            refreshed = auth.refresh(account["refresh_token"]).as_account()
            account.update(refreshed)
            self._save()
        return account

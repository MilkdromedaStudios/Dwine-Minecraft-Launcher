"""Skin & cape changer via the official Minecraft services API.

Skins are changed exactly the way the vanilla launcher does it —
authenticated calls to api.minecraftservices.com. Official capes owned
by the account can be selected; Dwine's own cosmetic capes are separate
(client-side only, see the `capes` feature).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.http import session

API = "https://api.minecraftservices.com"


def _headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def profile(access_token: str) -> dict[str, Any]:
    resp = session().get(
        f"{API}/minecraft/profile", headers=_headers(access_token), timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def upload_skin(access_token: str, png_path: Path, variant: str = "classic") -> None:
    """Upload a skin file. ``variant`` is 'classic' or 'slim'."""
    if variant not in ("classic", "slim"):
        raise ValueError("variant must be 'classic' or 'slim'")
    with open(png_path, "rb") as fh:
        resp = session().post(
            f"{API}/minecraft/profile/skins",
            headers=_headers(access_token),
            data={"variant": variant},
            files={"file": (Path(png_path).name, fh, "image/png")},
            timeout=60,
        )
    resp.raise_for_status()


def reset_skin(access_token: str) -> None:
    resp = session().delete(
        f"{API}/minecraft/profile/skins/active",
        headers=_headers(access_token),
        timeout=30,
    )
    resp.raise_for_status()


def owned_capes(access_token: str) -> list[dict[str, Any]]:
    return profile(access_token).get("capes", [])


def set_cape(access_token: str, cape_id: str | None) -> None:
    """Activate an owned cape, or hide the cape with ``None``."""
    if cape_id is None:
        resp = session().delete(
            f"{API}/minecraft/profile/capes/active",
            headers=_headers(access_token),
            timeout=30,
        )
    else:
        resp = session().put(
            f"{API}/minecraft/profile/capes/active",
            headers=_headers(access_token),
            json={"capeId": cape_id},
            timeout=30,
        )
    resp.raise_for_status()

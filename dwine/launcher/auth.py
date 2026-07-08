"""Microsoft account login — the official, Mojang-sanctioned flow.

Device-code OAuth -> Xbox Live -> XSTS -> Minecraft services token ->
profile. Tokens are refreshed automatically. Dwine never touches
passwords and never talks to unofficial endpoints, which is part of
what keeps it ban-safe.

You need an Azure application (client) ID with the
``XboxLive.signin offline_access`` scope. Create one for free at
https://portal.azure.com (Microsoft identity platform -> App
registrations, enable "Allow public client flows") and put the ID in
``settings.json`` under ``auth.client_id`` or the ``DWINE_MSA_CLIENT_ID``
environment variable.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Callable

from ..core.config import get_config
from ..core.http import session

DEVICE_CODE_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode"
TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
XBL_AUTH_URL = "https://user.auth.xboxlive.com/user/authenticate"
XSTS_AUTH_URL = "https://xsts.auth.xboxlive.com/xsts/authorize"
MC_LOGIN_URL = "https://api.minecraftservices.com/authentication/login_with_xbox"
MC_PROFILE_URL = "https://api.minecraftservices.com/minecraft/profile"
SCOPE = "XboxLive.signin offline_access"


class AuthError(RuntimeError):
    pass


@dataclass
class Session:
    name: str
    uuid: str
    access_token: str
    refresh_token: str
    xuid: str
    expires_at: float

    def as_account(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "uuid": self.uuid,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "xuid": self.xuid,
            "expires_at": self.expires_at,
            "user_type": "msa",
        }


def _client_id() -> str:
    client_id = os.environ.get("DWINE_MSA_CLIENT_ID") or get_config().get(
        "auth.client_id", ""
    )
    if not client_id:
        raise AuthError(
            "No Microsoft client ID configured. Register a free Azure app "
            "(see dwine/launcher/auth.py docstring) and set auth.client_id "
            "in settings.json or the DWINE_MSA_CLIENT_ID environment variable."
        )
    return client_id


def _post_json(url: str, **kwargs: Any) -> dict[str, Any]:
    resp = session().post(url, timeout=30, **kwargs)
    if resp.status_code >= 400:
        raise AuthError(f"{url} -> {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def start_device_login(
    on_code: Callable[[str, str], None],
    poll_timeout: int = 900,
) -> Session:
    """Interactive login. ``on_code(verification_url, user_code)`` shows the prompt."""
    client_id = _client_id()
    try:
        device = _post_json(
            DEVICE_CODE_URL, data={"client_id": client_id, "scope": SCOPE}
        )
    except AuthError as exc:
        if "unauthorized_client" in str(exc) or "invalid_client" in str(exc):
            raise AuthError(
                "Microsoft rejected the client ID. Check auth.client_id and "
                "make sure the Azure app has 'Allow public client flows' "
                "enabled (Authentication tab)."
            ) from exc
        raise
    on_code(device["verification_uri"], device["user_code"])

    interval = int(device.get("interval", 5))
    deadline = time.time() + min(poll_timeout, int(device.get("expires_in", 900)))
    while time.time() < deadline:
        time.sleep(interval)
        resp = session().post(
            TOKEN_URL,
            data={
                "client_id": client_id,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device["device_code"],
            },
            timeout=30,
        )
        try:
            body = resp.json()
        except ValueError:  # transient gateway hiccup: keep polling
            continue
        if resp.status_code == 200:
            return _finish_microsoft_login(body)
        error = body.get("error", "")
        if error in ("authorization_pending", "slow_down"):
            if error == "slow_down":
                interval += 5
            continue
        if error == "expired_token":
            raise AuthError("The code expired before it was entered — try again.")
        if error == "authorization_declined":
            raise AuthError("Sign-in was declined in the browser.")
        raise AuthError(f"Microsoft login failed: {error or resp.status_code}")
    raise AuthError("Login timed out — the code was never entered.")


def refresh(refresh_token: str) -> Session:
    body = _post_json(
        TOKEN_URL,
        data={
            "client_id": _client_id(),
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": SCOPE,
        },
    )
    return _finish_microsoft_login(body)


def _finish_microsoft_login(ms_tokens: dict[str, Any]) -> Session:
    ms_access = ms_tokens["access_token"]
    ms_refresh = ms_tokens.get("refresh_token", "")

    xbl = _post_json(
        XBL_AUTH_URL,
        json={
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": f"d={ms_access}",
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT",
        },
    )
    xbl_token = xbl["Token"]
    user_hash = xbl["DisplayClaims"]["xui"][0]["uhs"]

    xsts = session().post(
        XSTS_AUTH_URL,
        json={
            "Properties": {"SandboxId": "RETAIL", "UserTokens": [xbl_token]},
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT",
        },
        timeout=30,
    )
    if xsts.status_code == 401:
        xerr = xsts.json().get("XErr")
        hints = {
            2148916233: "This Microsoft account has no Xbox profile — create one at xbox.com.",
            2148916235: "Xbox Live is not available in this account's region.",
            2148916238: "This is a child account — it must be added to a family by an adult.",
        }
        raise AuthError(hints.get(xerr, f"XSTS denied the login (XErr {xerr})."))
    xsts.raise_for_status()
    xsts_body = xsts.json()
    xuid = xsts_body["DisplayClaims"]["xui"][0].get("xid", "")

    mc = _post_json(
        MC_LOGIN_URL,
        json={"identityToken": f"XBL3.0 x={user_hash};{xsts_body['Token']}"},
    )
    mc_token = mc["access_token"]
    expires_at = time.time() + int(mc.get("expires_in", 86400)) - 120

    profile_resp = session().get(
        MC_PROFILE_URL,
        headers={"Authorization": f"Bearer {mc_token}"},
        timeout=30,
    )
    if profile_resp.status_code == 404:
        raise AuthError(
            "This Microsoft account does not own Minecraft: Java Edition."
        )
    profile_resp.raise_for_status()
    profile = profile_resp.json()

    return Session(
        name=profile["name"],
        uuid=profile["id"],
        access_token=mc_token,
        refresh_token=ms_refresh,
        xuid=xuid,
        expires_at=expires_at,
    )


def offline_session(name: str = "Player") -> dict[str, Any]:
    """Deterministic offline account for singleplayer testing/dev only."""
    import hashlib
    import uuid as uuid_mod

    digest = hashlib.md5(f"OfflinePlayer:{name}".encode()).digest()
    raw = bytearray(digest)
    raw[6] = (raw[6] & 0x0F) | 0x30  # version 3 UUID, like vanilla offline mode
    raw[8] = (raw[8] & 0x3F) | 0x80
    return {
        "name": name,
        "uuid": uuid_mod.UUID(bytes=bytes(raw)).hex,
        "access_token": "0",
        "refresh_token": "",
        "xuid": "0",
        "expires_at": 0,
        "user_type": "legacy",
    }

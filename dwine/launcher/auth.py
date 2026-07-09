"""Microsoft account login — the official, Mojang-sanctioned flow.

Device-code OAuth -> Xbox Live -> XSTS -> Minecraft services token ->
profile. Tokens are refreshed automatically. Dwine never touches
passwords and never talks to unofficial endpoints, which is part of
what keeps it ban-safe.

Two ways to sign in, both device-code ("link code") flows:

* **Built-in (default, zero setup).** Dwine uses the official Minecraft
  launcher's public client ID against Microsoft's consumer OAuth
  endpoints (``login.live.com``). You get a short code, enter it at
  https://www.microsoft.com/link, and you're in. This is the same
  mechanism the vanilla ecosystem (consoles, mineflayer, prismarine)
  uses — no Azure account, no app registration.

* **Custom Azure app (optional).** If you prefer your auth traffic on
  your own app registration, set ``auth.client_id`` in ``settings.json``
  or the ``DWINE_MSA_CLIENT_ID`` environment variable to an Azure
  application (client) ID with the ``XboxLive.signin offline_access``
  scope, and Dwine uses it instead. New Azure client IDs must be
  allow-listed by Mojang once (free form: https://aka.ms/mce-reviewappid)
  before api.minecraftservices.com accepts them.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Callable

from ..core.config import get_config
from ..core.http import session

# -- built-in "link code" flow (no setup) ------------------------------------
# Public client ID of the official Minecraft launcher; used with
# Microsoft's consumer device-code endpoints. Verification happens at
# https://www.microsoft.com/link.
LINK_CLIENT_ID = "00000000402b5328"
LINK_DEVICE_CODE_URL = "https://login.live.com/oauth20_connect.srf"
LINK_TOKEN_URL = "https://login.live.com/oauth20_token.srf"
LINK_SCOPE = "service::user.auth.xboxlive.com::MBI_SSL"

# -- custom Azure app flow (optional) -----------------------------------------
DEVICE_CODE_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode"
TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
SCOPE = "XboxLive.signin offline_access"

XBL_AUTH_URL = "https://user.auth.xboxlive.com/user/authenticate"
XSTS_AUTH_URL = "https://xsts.auth.xboxlive.com/xsts/authorize"
MC_LOGIN_URL = "https://api.minecraftservices.com/authentication/login_with_xbox"
MC_PROFILE_URL = "https://api.minecraftservices.com/minecraft/profile"

FLOW_LINK = "link"
FLOW_AZURE = "azure"


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
    flow: str = FLOW_LINK

    def as_account(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "uuid": self.uuid,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "xuid": self.xuid,
            "expires_at": self.expires_at,
            "user_type": "msa",
            "auth_flow": self.flow,
        }


def _custom_client_id() -> str:
    """The user's own Azure app ID, if they configured one ("" otherwise)."""
    return os.environ.get("DWINE_MSA_CLIENT_ID") or get_config().get(
        "auth.client_id", ""
    )


def default_flow() -> str:
    """Link-code flow unless the user brought their own Azure app."""
    return FLOW_AZURE if _custom_client_id() else FLOW_LINK


def _post_json(url: str, **kwargs: Any) -> dict[str, Any]:
    resp = session().post(url, timeout=30, **kwargs)
    if resp.status_code >= 400:
        raise AuthError(f"{url} -> {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def start_device_login(
    on_code: Callable[[str, str], None],
    poll_timeout: int = 900,
    flow: str | None = None,
) -> Session:
    """Interactive login. ``on_code(verification_url, user_code)`` shows the prompt."""
    flow = flow or default_flow()
    if flow == FLOW_LINK:
        client_id = LINK_CLIENT_ID
        device_url, token_url, scope = LINK_DEVICE_CODE_URL, LINK_TOKEN_URL, LINK_SCOPE
        request = {"client_id": client_id, "scope": scope,
                   "response_type": "device_code"}
    else:
        client_id = _custom_client_id()
        if not client_id:
            raise AuthError(
                "No Azure client ID configured — use the built-in link-code "
                "login, or set auth.client_id / DWINE_MSA_CLIENT_ID."
            )
        device_url, token_url, scope = DEVICE_CODE_URL, TOKEN_URL, SCOPE
        request = {"client_id": client_id, "scope": scope}

    try:
        device = _post_json(device_url, data=request)
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
            token_url,
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
            return _finish_microsoft_login(body, flow)
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


def refresh(refresh_token: str, flow: str = FLOW_LINK) -> Session:
    if flow == FLOW_AZURE:
        token_url, client_id, scope = TOKEN_URL, _custom_client_id(), SCOPE
        if not client_id:
            raise AuthError(
                "This account was added with a custom Azure app, but no "
                "auth.client_id is configured any more — sign in again."
            )
    else:
        token_url, client_id, scope = LINK_TOKEN_URL, LINK_CLIENT_ID, LINK_SCOPE
    body = _post_json(
        token_url,
        data={
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": scope,
        },
    )
    return _finish_microsoft_login(body, flow)


def _finish_microsoft_login(ms_tokens: dict[str, Any], flow: str) -> Session:
    ms_access = ms_tokens["access_token"]
    ms_refresh = ms_tokens.get("refresh_token", "")

    # Azure AAD tokens are presented to Xbox Live with a "d=" prefix,
    # legacy consumer (login.live.com) tokens with "t=".
    rps_prefix = "d" if flow == FLOW_AZURE else "t"
    xbl = _post_json(
        XBL_AUTH_URL,
        json={
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": f"{rps_prefix}={ms_access}",
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

    try:
        mc = _post_json(
            MC_LOGIN_URL,
            json={"identityToken": f"XBL3.0 x={user_hash};{xsts_body['Token']}"},
        )
    except AuthError as exc:
        if f"{MC_LOGIN_URL} -> 403" in str(exc):
            raise AuthError(
                "Minecraft services refused this client ID (HTTP 403). "
                "Custom Azure app IDs must be allow-listed by Mojang once — "
                "submit the free form at https://aka.ms/mce-reviewappid, or "
                "just use the built-in link-code login."
            ) from exc
        raise
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
        flow=flow,
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

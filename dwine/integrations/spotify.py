"""Spotify integration for the music miniplayer.

Implements the Authorization-Code-with-PKCE flow with plain requests —
no client secret needed, tokens stay on the user's machine. The user
supplies their own (free) Spotify app client ID in settings.
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import json
import secrets
import threading
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass
from typing import Any

from ..core import paths
from ..core.config import get_config
from ..core.http import session

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API = "https://api.spotify.com/v1"
REDIRECT_PORT = 8858
REDIRECT_URI = f"http://127.0.0.1:{REDIRECT_PORT}/callback"
SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing"


@dataclass
class Track:
    title: str
    artist: str
    album: str
    progress_ms: int
    duration_ms: int
    playing: bool
    art_url: str = ""


class SpotifyClient:
    def __init__(self) -> None:
        self._tokens_path = paths.data_dir() / "spotify_tokens.json"
        self._tokens: dict[str, Any] = {}
        if self._tokens_path.exists():
            try:
                self._tokens = json.loads(self._tokens_path.read_text("utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

    @property
    def _client_id(self) -> str:
        client_id = get_config().get("integrations.spotify.client_id", "")
        if not client_id:
            raise RuntimeError(
                "Set integrations.spotify.client_id in settings — create a "
                "free app at developer.spotify.com and add "
                f"{REDIRECT_URI} as a redirect URI."
            )
        return client_id

    def _save_tokens(self) -> None:
        self._tokens_path.write_text(json.dumps(self._tokens), encoding="utf-8")
        try:
            self._tokens_path.chmod(0o600)
        except OSError:
            pass

    # -- auth ----------------------------------------------------------

    def login(self, open_browser: bool = True, timeout: int = 300) -> bool:
        verifier = secrets.token_urlsafe(64)[:128]
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        state = secrets.token_urlsafe(16)
        url = AUTH_URL + "?" + urllib.parse.urlencode(
            {
                "client_id": self._client_id,
                "response_type": "code",
                "redirect_uri": REDIRECT_URI,
                "scope": SCOPES,
                "code_challenge_method": "S256",
                "code_challenge": challenge,
                "state": state,
            }
        )

        result: dict[str, str] = {}
        done = threading.Event()

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                if query.get("state", [""])[0] == state and "code" in query:
                    result["code"] = query["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<h2>Dwine is connected to Spotify.</h2>You can close this tab."
                )
                done.set()

            def log_message(self, *args: Any) -> None:
                pass

        server = http.server.HTTPServer(("127.0.0.1", REDIRECT_PORT), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            if open_browser:
                webbrowser.open(url)
            if not done.wait(timeout) or "code" not in result:
                return False
        finally:
            server.shutdown()

        resp = session().post(
            TOKEN_URL,
            data={
                "client_id": self._client_id,
                "grant_type": "authorization_code",
                "code": result["code"],
                "redirect_uri": REDIRECT_URI,
                "code_verifier": verifier,
            },
            timeout=30,
        )
        resp.raise_for_status()
        self._store(resp.json())
        return True

    def _store(self, body: dict[str, Any]) -> None:
        self._tokens = {
            "access_token": body["access_token"],
            "refresh_token": body.get(
                "refresh_token", self._tokens.get("refresh_token", "")
            ),
            "expires_at": time.time() + int(body.get("expires_in", 3600)) - 60,
        }
        self._save_tokens()

    def _access_token(self) -> str | None:
        if not self._tokens:
            return None
        if time.time() >= float(self._tokens.get("expires_at", 0)):
            resp = session().post(
                TOKEN_URL,
                data={
                    "client_id": self._client_id,
                    "grant_type": "refresh_token",
                    "refresh_token": self._tokens.get("refresh_token", ""),
                },
                timeout=30,
            )
            if resp.status_code != 200:
                return None
            self._store(resp.json())
        return self._tokens["access_token"]

    # -- playback -------------------------------------------------------

    def _call(self, method: str, path: str, **kwargs: Any):
        token = self._access_token()
        if not token:
            return None
        return session().request(
            method,
            API + path,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
            **kwargs,
        )

    def now_playing(self) -> Track | None:
        resp = self._call("GET", "/me/player/currently-playing")
        if resp is None or resp.status_code != 200 or not resp.content:
            return None
        data = resp.json()
        item = data.get("item") or {}
        images = (item.get("album") or {}).get("images") or []
        return Track(
            title=item.get("name", ""),
            artist=", ".join(a["name"] for a in item.get("artists", [])),
            album=(item.get("album") or {}).get("name", ""),
            progress_ms=int(data.get("progress_ms") or 0),
            duration_ms=int(item.get("duration_ms") or 0),
            playing=bool(data.get("is_playing")),
            art_url=images[0]["url"] if images else "",
        )

    def play(self) -> None:
        self._call("PUT", "/me/player/play")

    def pause(self) -> None:
        self._call("PUT", "/me/player/pause")

    def next(self) -> None:
        self._call("POST", "/me/player/next")

    def previous(self) -> None:
        self._call("POST", "/me/player/previous")

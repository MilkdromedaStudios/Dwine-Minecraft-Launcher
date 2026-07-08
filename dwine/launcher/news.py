"""News panel + patch notes feeds.

News comes from a JSON feed (configurable URL, cached for offline use);
patch notes combine Dwine's own release notes with Mojang version dates.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from ..core import paths
from ..core.config import get_config
from ..core.http import get_json


@dataclass
class NewsItem:
    title: str
    body: str
    date: str
    url: str = ""
    image: str = ""
    tag: str = "news"


_FALLBACK: list[dict[str, Any]] = [
    {
        "title": "Welcome to Dwine",
        "body": "Your launcher is ready. Create a profile, pick a theme, and "
        "hit Play. Everything Dwine installs is legitimate and rule-compliant.",
        "date": "2026-01-01",
        "tag": "welcome",
    },
    {
        "title": "One-click performance",
        "body": "The FPS Mode preset installs Sodium, Lithium, FerriteCore, "
        "Entity Culling and more — matched to your exact Minecraft version.",
        "date": "2026-01-01",
        "tag": "tips",
    },
]


def fetch_news(force: bool = False) -> list[NewsItem]:
    cache = paths.cache_dir() / "news.json"
    data: list[dict[str, Any]] | None = None
    if not force and cache.exists() and time.time() - cache.stat().st_mtime < 1800:
        try:
            data = json.loads(cache.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = None
    if data is None:
        url = get_config().get("news.feed_url", "")
        try:
            fetched = get_json(url) if url else []
            data = fetched.get("items", fetched) if isinstance(fetched, dict) else fetched
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(data), encoding="utf-8")
        except Exception:
            if cache.exists():
                try:
                    data = json.loads(cache.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    data = None
            if data is None:
                data = _FALLBACK
    return [
        NewsItem(
            title=item.get("title", ""),
            body=item.get("body", ""),
            date=item.get("date", ""),
            url=item.get("url", ""),
            image=item.get("image", ""),
            tag=item.get("tag", "news"),
        )
        for item in data
    ]


def patch_notes() -> str:
    """Dwine's own changelog, bundled with the install."""
    from pathlib import Path

    for candidate in (
        Path(__file__).resolve().parent.parent.parent / "CHANGELOG.md",
        paths.data_dir() / "CHANGELOG.md",
    ):
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    return "# Patch notes\n\nNo changelog found for this build."

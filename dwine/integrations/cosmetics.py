"""Free cosmetics: client-side capes and visual flair.

Every cosmetic is free and client-side (rendered by the Dwine companion
mod for you and other Dwine users; invisible to everyone else, so no
server rules are involved). The index is a plain JSON feed; anyone can
contribute cosmetics via pull request.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..core import paths
from ..core.config import get_config
from ..core.http import download, get_json

INDEX_URL = (
    "https://raw.githubusercontent.com/MilkdromedaStudios/Dwine/main/"
    "cosmetics/index.json"
)

BUILTIN_CAPES: list[dict[str, str]] = [
    {"id": "dwine-classic", "name": "Dwine Classic", "kind": "cape"},
    {"id": "nebula", "name": "Nebula", "kind": "cape"},
    {"id": "ember", "name": "Ember", "kind": "cape"},
    {"id": "circuit", "name": "Circuit", "kind": "cape"},
]


@dataclass
class Cosmetic:
    id: str
    name: str
    kind: str  # cape | hat | trail
    url: str = ""


def _store() -> Path:
    folder = paths.data_dir() / "cosmetics"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def catalog() -> list[Cosmetic]:
    items = list(BUILTIN_CAPES)
    try:
        remote = get_json(INDEX_URL)
        items += remote.get("items", []) if isinstance(remote, dict) else remote
    except Exception:
        pass  # offline: builtins only
    seen: set[str] = set()
    result = []
    for item in items:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        result.append(
            Cosmetic(
                id=item["id"],
                name=item.get("name", item["id"]),
                kind=item.get("kind", "cape"),
                url=item.get("url", ""),
            )
        )
    return result


def _generate_builtin_cape(cosmetic_id: str, dest: Path) -> Path:
    """Builtin capes are generated locally — 64x32 classic cape layout."""
    from PIL import Image, ImageDraw

    palettes = {
        "dwine-classic": ("#0E1116", "#4F8CFF"),
        "nebula": ("#120B24", "#B18CFF"),
        "ember": ("#1B0F08", "#FF7A3C"),
        "circuit": ("#07110D", "#00FFD1"),
    }
    base, accent = palettes.get(cosmetic_id, ("#0E1116", "#4F8CFF"))

    def rgb(hex_color: str) -> tuple[int, int, int, int]:
        c = hex_color.lstrip("#")
        return tuple(int(c[i : i + 2], 16) for i in (0, 2, 4)) + (255,)

    image = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((1, 1, 21, 17), fill=rgb(base))  # cape front region
    draw.rectangle((2, 3, 20, 5), fill=rgb(accent))
    draw.rectangle((9, 6, 13, 14), fill=rgb(accent))
    image.save(dest, "PNG")
    return dest


def install(cosmetic: Cosmetic) -> Path:
    dest = _store() / f"{cosmetic.id}.png"
    if dest.exists():
        return dest
    if cosmetic.url:
        return download(cosmetic.url, dest)
    return _generate_builtin_cape(cosmetic.id, dest)


def equip(cosmetic_id: str | None) -> None:
    """Set (or clear) the active cape; the companion mod reads this config."""
    cfg = get_config()
    cfg.set("features.capes.active", cosmetic_id or "")
    state = {"active": cosmetic_id or "", "kind": "cape"}
    (_store() / "equipped.json").write_text(json.dumps(state), encoding="utf-8")

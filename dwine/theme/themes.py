"""Built-in Dwine themes.

A theme is pure data: the launcher renders it as QSS, and
:mod:`dwine.theme.mcpack` renders the same palette into an in-game
resource pack. Users can drop extra ``*.json`` themes into the themes
directory; they're merged over ``BASE`` so partial themes are fine.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core import paths

BASE: dict[str, Any] = {
    "dark": True,
    "radius": 10,
    "font": "Inter, Segoe UI, SF Pro Display, sans-serif",
    "glass": False,
    "glass_opacity": 0.82,
    "animations": True,
    "colors": {
        "bg": "#0E1116",
        "bg_alt": "#151A21",
        "surface": "#1B222C",
        "surface_alt": "#232C38",
        "text": "#E8EDF4",
        "text_dim": "#8A94A6",
        "accent": "#4F8CFF",
        "accent_hover": "#6EA1FF",
        "accent_text": "#FFFFFF",
        "success": "#3DDC97",
        "warning": "#FFC960",
        "danger": "#FF5D73",
        "border": "#2A3442",
    },
    "background": {
        "type": "gradient",
        "from": "#0E1116",
        "to": "#131B2A",
        "angle": 135,
    },
}

BUILTIN: dict[str, dict[str, Any]] = {
    "dwine-dark": {
        "display_name": "Dwine Dark",
        "description": "The signature look: deep slate with electric blue.",
    },
    "dwine-light": {
        "display_name": "Dwine Light",
        "description": "Clean paper-white with sapphire accents.",
        "dark": False,
        "colors": {
            "bg": "#F5F7FA",
            "bg_alt": "#ECF0F5",
            "surface": "#FFFFFF",
            "surface_alt": "#F0F3F8",
            "text": "#1A2230",
            "text_dim": "#5D6B80",
            "accent": "#2F6FED",
            "accent_hover": "#4C86F5",
            "accent_text": "#FFFFFF",
            "border": "#D7DEE8",
        },
        "background": {"type": "gradient", "from": "#F5F7FA", "to": "#E8EEF9",
                       "angle": 135},
    },
    "neon": {
        "display_name": "Neon",
        "description": "Cyber grid: near-black with cyan and magenta glow.",
        "colors": {
            "bg": "#07080D",
            "bg_alt": "#0C0E16",
            "surface": "#12141F",
            "surface_alt": "#191C2B",
            "text": "#EAF6FF",
            "text_dim": "#6C7A9C",
            "accent": "#00FFD1",
            "accent_hover": "#5CFFE2",
            "accent_text": "#03110D",
            "danger": "#FF3B8D",
            "border": "#232842",
        },
        "background": {"type": "gradient", "from": "#07080D", "to": "#120B24",
                       "angle": 160},
    },
    "minimal": {
        "display_name": "Minimal",
        "description": "Monochrome, borderless, zero noise.",
        "radius": 4,
        "colors": {
            "bg": "#101010",
            "bg_alt": "#141414",
            "surface": "#191919",
            "surface_alt": "#202020",
            "text": "#F2F2F2",
            "text_dim": "#7E7E7E",
            "accent": "#FFFFFF",
            "accent_hover": "#DDDDDD",
            "accent_text": "#101010",
            "border": "#262626",
        },
        "background": {"type": "solid", "from": "#101010", "to": "#101010",
                       "angle": 0},
    },
    "glass": {
        "display_name": "Glass",
        "description": "Frosted translucent panels over your wallpaper.",
        "glass": True,
        "glass_opacity": 0.72,
        "radius": 14,
        "colors": {
            "bg": "#10141B",
            "bg_alt": "#161B24",
            "surface": "#1D2430",
            "surface_alt": "#26303F",
            "text": "#F0F4FA",
            "text_dim": "#93A0B5",
            "accent": "#7FB4FF",
            "accent_hover": "#9CC6FF",
            "accent_text": "#0D1420",
            "border": "#33405233",
        },
        "background": {"type": "gradient", "from": "#182338", "to": "#0E1015",
                       "angle": 120},
    },
    "ember": {
        "display_name": "Ember",
        "description": "Warm charcoal with molten orange highlights.",
        "colors": {
            "bg": "#141110",
            "bg_alt": "#1A1614",
            "surface": "#221C19",
            "surface_alt": "#2C2420",
            "text": "#F5EDE8",
            "text_dim": "#9C8D83",
            "accent": "#FF7A3C",
            "accent_hover": "#FF9663",
            "accent_text": "#1B0F08",
            "border": "#3A2F28",
        },
        "background": {"type": "gradient", "from": "#141110", "to": "#241108",
                       "angle": 135},
    },
}


def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


@dataclass
class Theme:
    name: str
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        return self.data.get("display_name", self.name)

    @property
    def colors(self) -> dict[str, str]:
        return self.data["colors"]

    def color(self, key: str) -> str:
        return self.data["colors"][key]

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


def list_themes() -> list[str]:
    names = list(BUILTIN)
    directory = paths.themes_dir()
    if directory.exists():
        for file in sorted(directory.glob("*.json")):
            if file.stem not in names:
                names.append(file.stem)
    return names


def load_theme(name: str) -> Theme:
    if name in BUILTIN:
        return Theme(name=name, data=_merge(BASE, BUILTIN[name]))
    custom = paths.themes_dir() / f"{name}.json"
    if custom.exists():
        data = json.loads(custom.read_text(encoding="utf-8"))
        return Theme(name=name, data=_merge(BASE, data))
    return Theme(name="dwine-dark", data=_merge(BASE, BUILTIN["dwine-dark"]))


def save_custom_theme(name: str, data: dict[str, Any]) -> Path:
    directory = paths.themes_dir()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{name}.json"
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return target

"""HUD layout model for the drag-and-drop editor.

Elements are anchored to one of nine screen anchors with pixel offsets,
so layouts scale across resolutions and GUI scales. The layout is
written to ``config/dwine/hud.json`` inside the profile's game directory,
where the Dwine companion mod (and HUD mods that support it) read it.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

ANCHORS = (
    "top_left", "top_center", "top_right",
    "middle_left", "middle_center", "middle_right",
    "bottom_left", "bottom_center", "bottom_right",
)

ELEMENT_TYPES = (
    "fps", "ping", "cps", "memory", "coordinates", "direction",
    "keystrokes", "armor_status", "potion_effects", "clock",
    "day_counter", "server_ip", "music_player", "sprint_indicator",
    "sneak_indicator", "combo_counter", "saturation", "biome",
    "compass", "speed", "stopwatch", "match_timer", "hit_distance",
    "hit_delay", "block_hit_delay", "server_info", "fps_graph",
    "chunk_graph", "party_list", "cooldown",
)


@dataclass
class HudElement:
    type: str
    anchor: str = "top_left"
    offset_x: int = 4
    offset_y: int = 4
    scale: float = 1.0
    visible: bool = True
    color: str = "#FFFFFF"
    background: bool = True
    options: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.anchor not in ANCHORS:
            raise ValueError(f"bad anchor {self.anchor!r}; expected one of {ANCHORS}")
        if self.type not in ELEMENT_TYPES:
            raise ValueError(f"unknown HUD element type {self.type!r}")


@dataclass
class HudLayout:
    name: str = "default"
    elements: list[HudElement] = field(default_factory=list)

    def add(self, element: HudElement) -> None:
        self.elements.append(element)

    def remove(self, element_type: str) -> None:
        self.elements = [e for e in self.elements if e.type != element_type]

    def to_dict(self) -> dict:
        return {"name": self.name, "elements": [asdict(e) for e in self.elements]}

    @classmethod
    def from_dict(cls, data: dict) -> "HudLayout":
        return cls(
            name=data.get("name", "default"),
            elements=[HudElement(**e) for e in data.get("elements", [])],
        )

    def save(self, game_dir: Path) -> Path:
        target = Path(game_dir) / "config" / "dwine" / "hud.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return target

    @classmethod
    def load(cls, game_dir: Path) -> "HudLayout":
        target = Path(game_dir) / "config" / "dwine" / "hud.json"
        if target.exists():
            return cls.from_dict(json.loads(target.read_text(encoding="utf-8")))
        return default_layout()


def default_layout() -> HudLayout:
    return HudLayout(
        name="default",
        elements=[
            HudElement("fps", anchor="top_left", offset_x=4, offset_y=4),
            HudElement("ping", anchor="top_left", offset_x=4, offset_y=42),
            HudElement("coordinates", anchor="bottom_left", offset_x=4, offset_y=-4),
            HudElement("keystrokes", anchor="bottom_right", offset_x=-8, offset_y=-8,
                       visible=False),
            HudElement("armor_status", anchor="middle_left", offset_x=4, offset_y=0,
                       visible=False),
            HudElement("music_player", anchor="top_right", offset_x=-4, offset_y=4,
                       visible=False),
        ],
    )

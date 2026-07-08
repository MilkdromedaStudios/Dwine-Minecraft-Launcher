"""Crosshair editor: parametric crosshair rendered to a texture.

The generated PNG is injected into the Dwine theme resource pack, so the
custom crosshair works on every version and server — it's just a texture.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

SHAPES = ("cross", "dot", "circle", "square", "plus_dot", "chevron")


@dataclass
class Crosshair:
    shape: str = "cross"
    size: int = 15  # texture is size x size pixels (vanilla slot is 15x15)
    thickness: int = 1
    gap: int = 3
    color: str = "#FFFFFF"
    opacity: int = 255
    outline: bool = True
    outline_color: str = "#000000"
    animated: bool = False  # subtle pulse via mcmeta animation frames

    def __post_init__(self) -> None:
        if self.shape not in SHAPES:
            raise ValueError(f"unknown shape {self.shape!r}; expected one of {SHAPES}")
        self.size = max(7, min(31, int(self.size)))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Crosshair":
        known = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})

    # -- rendering -----------------------------------------------------

    def _rgba(self) -> tuple[int, int, int, int]:
        color = self.color.lstrip("#")
        r, g, b = (int(color[i : i + 2], 16) for i in (0, 2, 4))
        return (r, g, b, max(0, min(255, self.opacity)))

    def render(self, scale: int = 1):
        """Render to a PIL Image (requires Pillow)."""
        from PIL import Image, ImageDraw

        px = self.size * scale
        image = Image.new("RGBA", (px, px), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        rgba = self._rgba()
        outline_rgba = None
        if self.outline:
            oc = self.outline_color.lstrip("#")
            outline_rgba = tuple(int(oc[i : i + 2], 16) for i in (0, 2, 4)) + (rgba[3],)

        center = px // 2
        thick = max(1, self.thickness * scale)
        gap = self.gap * scale
        arm = center - 1

        def line(x0: int, y0: int, x1: int, y1: int) -> None:
            if outline_rgba:
                draw.rectangle(
                    (x0 - 1, y0 - 1, x1 + 1, y1 + 1), fill=outline_rgba
                )
            draw.rectangle((x0, y0, x1, y1), fill=rgba)

        half = thick // 2
        if self.shape in ("cross", "plus_dot"):
            line(center - half, 0, center + half, center - gap)  # up
            line(center - half, center + gap, center + half, px - 1)  # down
            line(0, center - half, center - gap, center + half)  # left
            line(center + gap, center - half, px - 1, center + half)  # right
        if self.shape in ("dot", "plus_dot"):
            line(center - half, center - half, center + half, center + half)
        if self.shape == "circle":
            width = max(1, thick)
            if outline_rgba:
                draw.ellipse((0, 0, px - 1, px - 1), outline=outline_rgba,
                             width=width + 2)
            draw.ellipse((1, 1, px - 2, px - 2), outline=rgba, width=width)
        if self.shape == "square":
            if outline_rgba:
                draw.rectangle((0, 0, px - 1, px - 1), outline=outline_rgba,
                               width=thick + 1)
            draw.rectangle((1, 1, px - 2, px - 2), outline=rgba, width=thick)
        if self.shape == "chevron":
            line(gap, center + arm // 2, center - half, center - half)
            line(center + half, center - half, px - 1 - gap, center + arm // 2)
        return image

    def save_png(self, dest: Path, scale: int = 1) -> Path:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        self.render(scale=scale).save(dest, "PNG")
        return dest


PRESETS: dict[str, Crosshair] = {
    "default": Crosshair(),
    "dot": Crosshair(shape="dot", thickness=2, outline=True),
    "neon-cross": Crosshair(shape="cross", color="#00FFD1", gap=4, outline=True),
    "sniper": Crosshair(shape="circle", color="#FF3355", thickness=1, outline=False),
    "quad": Crosshair(shape="plus_dot", color="#B18CFF", gap=5),
    "boxy": Crosshair(shape="square", color="#FFD166", thickness=1),
}


def save_config(crosshair: Crosshair, game_dir: Path) -> Path:
    target = Path(game_dir) / "config" / "dwine" / "crosshair.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(crosshair.to_dict(), indent=2), encoding="utf-8")
    return target

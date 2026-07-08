"""In-game theming: generates the "Dwine Theme" resource pack.

This is how Dwine restyles Minecraft itself without touching a single
byte of game code: the active launcher theme (plus the user's crosshair)
is rendered into an ordinary resource pack — buttons, hotbar, menu
backgrounds, crosshair — and dropped into the profile's resourcepacks
folder. Resource packs are 100%% server-legal everywhere.

Both texture layouts are emitted so one pack works across versions:

* legacy ``gui/widgets.png`` (≤ 1.20.1)
* modern ``gui/sprites/**`` (1.20.2+), with nine-slice metadata
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

from .. import __version__
from ..features.crosshair import Crosshair
from .themes import Theme

if TYPE_CHECKING:  # pragma: no cover
    from PIL import Image

PACK_NAME = "Dwine Theme.zip"

# Minecraft resource pack format by game version (newest match wins).
_PACK_FORMATS: list[tuple[tuple[int, int, int], int]] = [
    ((1, 6, 1), 1), ((1, 9, 0), 2), ((1, 11, 0), 3), ((1, 13, 0), 4),
    ((1, 15, 0), 5), ((1, 16, 2), 6), ((1, 17, 0), 7), ((1, 18, 0), 8),
    ((1, 19, 0), 9), ((1, 19, 3), 12), ((1, 19, 4), 13), ((1, 20, 0), 15),
    ((1, 20, 2), 18), ((1, 20, 3), 22), ((1, 20, 5), 32), ((1, 21, 0), 34),
    ((1, 21, 2), 42), ((1, 21, 4), 46), ((1, 21, 5), 55),
]


def _parse_version(mc_version: str) -> tuple[int, int, int]:
    match = re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", mc_version)
    if not match:
        return (1, 21, 0)  # snapshots and odd ids: assume modern
    return (int(match.group(1)), int(match.group(2)), int(match.group(3) or 0))


def pack_format_for(mc_version: str) -> int:
    version = _parse_version(mc_version)
    result = 1
    for threshold, fmt in _PACK_FORMATS:
        if version >= threshold:
            result = fmt
    return result


# -- drawing helpers ----------------------------------------------------

def _rgb(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    color = hex_color.lstrip("#")[:6]
    r, g, b = (int(color[i : i + 2], 16) for i in (0, 2, 4))
    return (r, g, b, alpha)


def _shade(rgba: tuple[int, int, int, int], factor: float) -> tuple[int, int, int, int]:
    r, g, b, a = rgba
    return (
        max(0, min(255, int(r * factor))),
        max(0, min(255, int(g * factor))),
        max(0, min(255, int(b * factor))),
        a,
    )


def _button(theme: Theme, state: str, size: tuple[int, int] = (200, 20)) -> "Image":
    from PIL import Image, ImageDraw

    surface = _rgb(theme.color("surface_alt"), 235)
    border = _rgb(theme.color("border"))
    if state == "hover":
        surface = _rgb(theme.color("accent"), 235)
        border = _rgb(theme.color("accent_hover"))
    elif state == "disabled":
        surface = _shade(_rgb(theme.color("surface"), 200), 0.7)
        border = _shade(border, 0.7)

    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    w, h = size
    draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=4, fill=surface,
                           outline=border, width=1)
    # Subtle top highlight for depth.
    highlight = _shade(surface, 1.25)
    draw.rounded_rectangle((1, 1, w - 2, h // 2), radius=3, fill=None,
                           outline=highlight, width=1)
    return image


def _hotbar(theme: Theme) -> "Image":
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (182, 22), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (0, 0, 181, 21), radius=5,
        fill=_rgb(theme.color("bg"), 170),
        outline=_rgb(theme.color("border"), 200), width=1,
    )
    for slot in range(1, 9):  # slot separators
        x = slot * 20
        draw.line((x, 3, x, 18), fill=_rgb(theme.color("border"), 90))
    return image


def _hotbar_selection(theme: Theme, size: tuple[int, int]) -> "Image":
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (0, 0, size[0] - 1, size[1] - 1), radius=6,
        outline=_rgb(theme.color("accent")), width=2,
    )
    return image


def _menu_tile(theme: Theme) -> "Image":
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (16, 16), _rgb(theme.color("bg")))
    draw = ImageDraw.Draw(image)
    draw.point((0, 0), fill=_shade(_rgb(theme.color("bg")), 1.15))
    draw.point((8, 8), fill=_shade(_rgb(theme.color("bg")), 0.9))
    return image


def _pack_icon(theme: Theme) -> "Image":
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (128, 128), _rgb(theme.color("bg")))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 119, 119), radius=28,
                           fill=_rgb(theme.color("surface")))
    # A stylized "D" monogram in the accent color.
    draw.rounded_rectangle((40, 32, 56, 96), radius=8,
                           fill=_rgb(theme.color("accent")))
    draw.arc((40, 32, 96, 96), start=-90, end=90,
             fill=_rgb(theme.color("accent")), width=15)
    return image


# -- pack assembly -------------------------------------------------------

def _png_bytes(image: "Image") -> bytes:
    import io

    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


NINE_SLICE_MCMETA = json.dumps(
    {
        "gui": {
            "scaling": {
                "type": "nine_slice",
                "width": 200,
                "height": 20,
                "border": 4,
            }
        }
    }
)


def build_pack(
    theme: Theme,
    mc_version: str,
    dest_dir: Path,
    crosshair: Crosshair | None = None,
) -> Path:
    """Render the theme into ``<dest_dir>/Dwine Theme.zip`` and return it."""
    from PIL import Image

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / PACK_NAME
    crosshair = crosshair or Crosshair()

    fmt = pack_format_for(mc_version)
    mcmeta = {
        "pack": {
            "pack_format": fmt,
            "supported_formats": {"min_inclusive": 1, "max_inclusive": 999},
            "description": f"§bDwine§r · {theme.display_name} · v{__version__}",
        }
    }

    # Legacy widgets.png: hotbar (0,0), selector (0,22), buttons y=46/66/86.
    widgets = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    widgets.paste(_hotbar(theme), (0, 0))
    widgets.paste(_hotbar_selection(theme, (24, 24)), (0, 22))
    widgets.paste(_button(theme, "disabled"), (0, 46))
    widgets.paste(_button(theme, "normal"), (0, 66))
    widgets.paste(_button(theme, "hover"), (0, 86))

    gui = "assets/minecraft/textures/gui"
    files: dict[str, bytes] = {
        "pack.mcmeta": json.dumps(mcmeta, indent=2).encode(),
        "pack.png": _png_bytes(_pack_icon(theme)),
        f"{gui}/widgets.png": _png_bytes(widgets),
        f"{gui}/options_background.png": _png_bytes(_menu_tile(theme)),
        f"{gui}/menu_background.png": _png_bytes(_menu_tile(theme)),
        # Modern sprite layout (1.20.2+)
        f"{gui}/sprites/widget/button.png": _png_bytes(_button(theme, "normal")),
        f"{gui}/sprites/widget/button.png.mcmeta": NINE_SLICE_MCMETA.encode(),
        f"{gui}/sprites/widget/button_disabled.png": _png_bytes(
            _button(theme, "disabled")
        ),
        f"{gui}/sprites/widget/button_disabled.png.mcmeta": NINE_SLICE_MCMETA.encode(),
        f"{gui}/sprites/widget/button_highlighted.png": _png_bytes(
            _button(theme, "hover")
        ),
        f"{gui}/sprites/widget/button_highlighted.png.mcmeta": NINE_SLICE_MCMETA.encode(),
        f"{gui}/sprites/hud/hotbar.png": _png_bytes(_hotbar(theme)),
        f"{gui}/sprites/hud/hotbar_selection.png": _png_bytes(
            _hotbar_selection(theme, (24, 23))
        ),
        f"{gui}/sprites/hud/crosshair.png": _png_bytes(crosshair.render()),
    }

    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, payload in files.items():
            zf.writestr(name, payload)
    return dest


def enable_in_options(game_dir: Path, pack_file: str = PACK_NAME) -> None:
    """Add the pack to options.txt so it's active on next launch."""
    options = Path(game_dir) / "options.txt"
    entry = f"file/{pack_file}"
    lines: list[str] = []
    if options.exists():
        lines = options.read_text(encoding="utf-8").splitlines()

    def _update(line: str) -> str:
        key, _, raw = line.partition(":")
        try:
            packs = json.loads(raw)
        except json.JSONDecodeError:
            packs = []
        if entry not in packs:
            packs.append(entry)
        return f"{key}:{json.dumps(packs)}"

    found = False
    for i, line in enumerate(lines):
        if line.startswith("resourcePacks:"):
            lines[i] = _update(line)
            found = True
    if not found:
        lines.append(f'resourcePacks:["vanilla",{json.dumps(entry)}]')
    options.parent.mkdir(parents=True, exist_ok=True)
    options.write_text("\n".join(lines) + "\n", encoding="utf-8")

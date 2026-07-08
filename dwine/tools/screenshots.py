"""Screenshot manager: gallery across profiles + a small Pillow editor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..core import paths
from ..launcher.profiles import Profile


@dataclass
class Shot:
    path: Path
    profile: str
    taken_at: float

    @property
    def name(self) -> str:
        return self.path.name


def gallery(profiles: list[Profile]) -> list[Shot]:
    """All screenshots, newest first, across every profile + Dwine's folder."""
    shots: list[Shot] = []
    sources: list[tuple[str, Path]] = [("dwine", paths.screenshots_dir())]
    sources += [(p.name, p.game_dir / "screenshots") for p in profiles]
    for profile_name, folder in sources:
        if not folder.exists():
            continue
        for file in folder.glob("*.png"):
            shots.append(
                Shot(path=file, profile=profile_name, taken_at=file.stat().st_mtime)
            )
    return sorted(shots, key=lambda s: s.taken_at, reverse=True)


def collect(profiles: list[Profile]) -> int:
    """Copy new screenshots from every profile into Dwine's gallery folder."""
    target = paths.screenshots_dir()
    target.mkdir(parents=True, exist_ok=True)
    copied = 0
    for shot in gallery(profiles):
        if shot.profile == "dwine":
            continue
        dest = target / f"{shot.profile}-{shot.name}"
        if not dest.exists():
            dest.write_bytes(shot.path.read_bytes())
            copied += 1
    return copied


# -- editor (Pillow) -----------------------------------------------------

def edit(
    source: Path,
    dest: Path | None = None,
    crop: tuple[int, int, int, int] | None = None,
    resize_percent: int = 0,
    caption: str = "",
    watermark: bool = False,
) -> Path:
    """Basic edits used by the gallery UI: crop, resize, caption, watermark."""
    from PIL import Image, ImageDraw

    source = Path(source)
    image = Image.open(source).convert("RGBA")
    if crop:
        image = image.crop(crop)
    if resize_percent and resize_percent != 100:
        w, h = image.size
        image = image.resize(
            (max(1, w * resize_percent // 100), max(1, h * resize_percent // 100)),
            Image.LANCZOS,
        )
    if caption or watermark:
        draw = ImageDraw.Draw(image)
        if caption:
            draw.text((12, image.height - 28), caption, fill=(255, 255, 255, 230))
        if watermark:
            draw.text(
                (image.width - 70, image.height - 22),
                "Dwine",
                fill=(255, 255, 255, 140),
            )
    dest = Path(dest) if dest else source.with_stem(source.stem + "-edited")
    image.save(dest, "PNG")
    return dest

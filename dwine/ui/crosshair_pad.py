"""The crosshair drawpad: paint your own crosshair, pixel by pixel.

Left-click (or drag) paints with the selected color, right-click erases.
Saving stores the pixels in ``crosshair.custom`` and switches
``crosshair.preset`` to ``custom`` so the next launch renders your
drawing into the theme resource pack.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.config import get_config
from ..features.crosshair import Crosshair
from .widgets import ColorSwatch

PALETTE = (
    "#FFFFFF", "#000000", "#FF5D73", "#FFD166", "#3DDC97",
    "#4F8CFF", "#B18CFF", "#00FFD1", "#FF9F1C", "#8A93A6",
)

CELL = 22  # on-screen pixels per crosshair pixel


def _starter_pixels(shape: str, size: int, color: str) -> dict[str, str]:
    """Algorithmic starting patterns so the pad never starts scary-blank."""
    center = size // 2
    gap = 2
    pixels: dict[str, str] = {}
    if shape in ("cross", "plus_dot"):
        for offset in range(gap + 1, center + 1):
            pixels[f"{center},{center - offset}"] = color
            pixels[f"{center},{center + offset}"] = color
            pixels[f"{center - offset},{center}"] = color
            pixels[f"{center + offset},{center}"] = color
    if shape in ("dot", "plus_dot"):
        pixels[f"{center},{center}"] = color
    if shape == "circle":
        radius = center - 1
        for x in range(size):
            for y in range(size):
                distance = ((x - center) ** 2 + (y - center) ** 2) ** 0.5
                if abs(distance - radius) < 0.6:
                    pixels[f"{x},{y}"] = color
    if shape == "square":
        for i in range(1, size - 1):
            pixels[f"{i},1"] = color
            pixels[f"{i},{size - 2}"] = color
            pixels[f"1,{i}"] = color
            pixels[f"{size - 2},{i}"] = color
    return pixels


class DrawpadCanvas(QWidget):
    changed = Signal()

    def __init__(self, size: int = 15, parent: QWidget | None = None):
        super().__init__(parent)
        self.grid = size
        self.pixels: dict[str, str] = {}
        self.brush = "#FFFFFF"
        self._painting = False
        self._erasing = False
        self.setFixedSize(size * CELL + 1, size * CELL + 1)

    def set_grid(self, size: int) -> None:
        self.grid = size
        self.pixels = {
            key: value for key, value in self.pixels.items()
            if all(0 <= int(part) < size for part in key.split(","))
        }
        self.setFixedSize(size * CELL + 1, size * CELL + 1)
        self.update()
        self.changed.emit()

    # -- painting --------------------------------------------------------

    def _cell_at(self, pos) -> tuple[int, int] | None:
        x, y = int(pos.x()) // CELL, int(pos.y()) // CELL
        if 0 <= x < self.grid and 0 <= y < self.grid:
            return x, y
        return None

    def _apply(self, pos) -> None:
        cell = self._cell_at(pos)
        if cell is None:
            return
        key = f"{cell[0]},{cell[1]}"
        if self._erasing:
            self.pixels.pop(key, None)
        else:
            self.pixels[key] = self.brush
        self.update()
        self.changed.emit()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._painting = True
        self._erasing = event.button() == Qt.MouseButton.RightButton
        self._apply(event.position())

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._painting:
            self._apply(event.position())

    def mouseReleaseEvent(self, _event) -> None:  # noqa: N802
        self._painting = False
        self._erasing = False

    # -- drawing -----------------------------------------------------------

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        # checkerboard = transparency
        for x in range(self.grid):
            for y in range(self.grid):
                shade = "#20262E" if (x + y) % 2 == 0 else "#181D24"
                painter.fillRect(x * CELL, y * CELL, CELL, CELL, QColor(shade))
        for key, hex_color in self.pixels.items():
            x, y = (int(part) for part in key.split(","))
            painter.fillRect(x * CELL, y * CELL, CELL, CELL, QColor(hex_color))
        # grid lines + center guides
        painter.setPen(QPen(QColor(255, 255, 255, 26)))
        for i in range(self.grid + 1):
            painter.drawLine(i * CELL, 0, i * CELL, self.grid * CELL)
            painter.drawLine(0, i * CELL, self.grid * CELL, i * CELL)
        center = self.grid // 2
        painter.setPen(QPen(QColor(79, 140, 255, 90)))
        painter.drawRect(center * CELL, center * CELL, CELL, CELL)


class CrosshairDrawpadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crosshair drawpad")
        cfg = get_config()
        stored = (cfg.get("crosshair.custom", {}) or {})
        size = int(stored.get("size", 15)) or 15

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        hint = QLabel("Left-click paints · drag to draw · right-click erases. "
                      "The blue box is the exact screen center.")
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        canvas_row = QHBoxLayout()
        canvas_row.addStretch(1)
        self.canvas = DrawpadCanvas(size)
        if stored.get("pixels"):
            self.canvas.pixels = dict(stored["pixels"])
        canvas_row.addWidget(self.canvas)
        canvas_row.addStretch(1)
        layout.addLayout(canvas_row)

        # -- palette -------------------------------------------------------
        palette_row = QHBoxLayout()
        palette_row.addWidget(QLabel("Color:"))
        self._swatches: list[ColorSwatch] = []
        for color in PALETTE:
            swatch = ColorSwatch(color, selected=color == self.canvas.brush)
            swatch.clicked.connect(self._pick_color)
            self._swatches.append(swatch)
            palette_row.addWidget(swatch)
        more = QPushButton("More …")
        more.clicked.connect(self._pick_custom_color)
        palette_row.addWidget(more)
        palette_row.addStretch(1)
        layout.addLayout(palette_row)

        # -- tools ------------------------------------------------------------
        tools = QHBoxLayout()
        tools.addWidget(QLabel("Canvas:"))
        self.size_box = QComboBox()
        for grid in (11, 15, 21, 31):
            self.size_box.addItem(f"{grid} × {grid}", grid)
            if grid == size:
                self.size_box.setCurrentIndex(self.size_box.count() - 1)
        self.size_box.currentIndexChanged.connect(
            lambda _i: self.canvas.set_grid(self.size_box.currentData()))
        tools.addWidget(self.size_box)

        tools.addWidget(QLabel("Start from:"))
        self.shape_box = QComboBox()
        for shape in ("cross", "plus_dot", "dot", "circle", "square"):
            self.shape_box.addItem(shape.replace("_", " + "), shape)
        load = QPushButton("Load shape")
        load.clicked.connect(self._load_shape)
        tools.addWidget(self.shape_box)
        tools.addWidget(load)

        clear = QPushButton("Clear")
        clear.clicked.connect(self._clear)
        tools.addWidget(clear)
        tools.addStretch(1)
        layout.addLayout(tools)

        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save crosshair")
        save.setObjectName("Primary")
        save.clicked.connect(self._save)
        actions.addWidget(cancel)
        actions.addWidget(save)
        layout.addLayout(actions)

    # ------------------------------------------------------------------

    def _pick_color(self, color: str) -> None:
        self.canvas.brush = color
        for swatch in self._swatches:
            swatch.selected = swatch.color == color
            swatch.update()

    def _pick_custom_color(self) -> None:
        from PySide6.QtWidgets import QColorDialog

        picked = QColorDialog.getColor(QColor(self.canvas.brush), self,
                                       "Brush color")
        if picked.isValid():
            self._pick_color(picked.name().upper())

    def _load_shape(self) -> None:
        self.canvas.pixels = _starter_pixels(
            self.shape_box.currentData(), self.canvas.grid, self.canvas.brush)
        self.canvas.update()

    def _clear(self) -> None:
        self.canvas.pixels = {}
        self.canvas.update()

    def _save(self) -> None:
        crosshair = Crosshair(
            shape="custom",
            size=self.canvas.grid,
            pixels=dict(self.canvas.pixels),
        )
        cfg = get_config()
        cfg.set("crosshair.custom", crosshair.to_dict(), save=False)
        cfg.set("crosshair.preset", "custom")
        self.accept()

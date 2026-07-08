"""HUD editor: a drag-and-drop canvas over a mock game frame.

Elements from the HUD layout model are drawn as movable chips; dragging
updates anchor + offset live, and Save writes ``config/dwine/hud.json``
into the selected profile.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...features.hud import ANCHORS, ELEMENT_TYPES, HudElement, HudLayout, default_layout
from ...launcher.profiles import ProfileStore

CHIP_SIZE = (110, 30)


def _anchor_point(anchor: str, width: int, height: int) -> QPoint:
    column = {"left": 0, "center": width // 2, "right": width}
    row = {"top": 0, "middle": height // 2, "bottom": height}
    vertical, horizontal = anchor.split("_")
    return QPoint(column[horizontal], row[vertical])


def _nearest_anchor(pos: QPoint, width: int, height: int) -> str:
    best, best_distance = "top_left", float("inf")
    for anchor in ANCHORS:
        point = _anchor_point(anchor, width, height)
        distance = (point.x() - pos.x()) ** 2 + (point.y() - pos.y()) ** 2
        if distance < best_distance:
            best, best_distance = anchor, distance
    return best


class HudCanvas(QWidget):
    def __init__(self, layout_model: HudLayout, parent=None):
        super().__init__(parent)
        self.model = layout_model
        self.setMinimumSize(640, 360)
        self._dragging: HudElement | None = None
        self._grab_offset = QPoint()

    # -- geometry --------------------------------------------------------

    def _element_rect(self, element: HudElement) -> QRect:
        origin = _anchor_point(element.anchor, self.width(), self.height())
        x = origin.x() + element.offset_x
        y = origin.y() + element.offset_y
        w, h = CHIP_SIZE
        if "right" in element.anchor:
            x -= w
        elif "center" in element.anchor:
            x -= w // 2
        if "bottom" in element.anchor:
            y -= h
        elif "middle" in element.anchor:
            y -= h // 2
        return QRect(x, y, w, h)

    # -- painting -----------------------------------------------------------

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#101418"))
        # mock horizon + hotbar so placement has context
        painter.setPen(QPen(QColor("#1E2833"), 2))
        painter.drawLine(0, int(self.height() * 0.62), self.width(),
                         int(self.height() * 0.62))
        painter.setBrush(QColor(20, 26, 33, 210))
        painter.setPen(QPen(QColor("#2A3442")))
        bar_w = 364
        painter.drawRoundedRect(
            (self.width() - bar_w) // 2, self.height() - 52, bar_w, 40, 8, 8
        )

        for element in self.model.elements:
            if not element.visible:
                continue
            rect = self._element_rect(element)
            active = element is self._dragging
            painter.setBrush(QColor(31, 41, 55, 235))
            painter.setPen(QPen(QColor("#4F8CFF" if active else "#2A3442"), 2))
            painter.drawRoundedRect(rect, 8, 8)
            painter.setPen(QPen(QColor(element.color)))
            painter.drawText(
                rect, Qt.AlignmentFlag.AlignCenter,
                element.type.replace("_", " "),
            )

    # -- dragging ------------------------------------------------------------

    def mousePressEvent(self, event) -> None:  # noqa: N802
        pos = event.position().toPoint()
        for element in reversed(self.model.elements):
            if element.visible and self._element_rect(element).contains(pos):
                self._dragging = element
                self._grab_offset = pos - self._element_rect(element).topLeft()
                self.update()
                return

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if not self._dragging:
            return
        pos = event.position().toPoint() - self._grab_offset
        center = pos + QPoint(CHIP_SIZE[0] // 2, CHIP_SIZE[1] // 2)
        anchor = _nearest_anchor(center, self.width(), self.height())
        origin = _anchor_point(anchor, self.width(), self.height())
        element = self._dragging
        element.anchor = anchor
        reference_x, reference_y = pos.x(), pos.y()
        if "right" in anchor:
            reference_x = pos.x() + CHIP_SIZE[0]
        elif "center" in anchor:
            reference_x = pos.x() + CHIP_SIZE[0] // 2
        if "bottom" in anchor:
            reference_y = pos.y() + CHIP_SIZE[1]
        elif "middle" in anchor:
            reference_y = pos.y() + CHIP_SIZE[1] // 2
        element.offset_x = reference_x - origin.x()
        element.offset_y = reference_y - origin.y()
        self.update()

    def mouseReleaseEvent(self, _event) -> None:  # noqa: N802
        self._dragging = None
        self.update()


class HudEditorPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.store = ProfileStore()
        self.model = default_layout()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)

        top = QHBoxLayout()
        top.addWidget(QLabel("Profile:"))
        self.profile_box = QComboBox()
        self.profile_box.currentIndexChanged.connect(self._load_layout)
        self.reload_profiles()
        top.addWidget(self.profile_box, 1)

        self.element_box = QComboBox()
        for element_type in ELEMENT_TYPES:
            self.element_box.addItem(element_type.replace("_", " "), element_type)
        add = QPushButton("+ Add element")
        add.clicked.connect(self._add_element)
        save = QPushButton("Save layout")
        save.setObjectName("Primary")
        save.clicked.connect(self._save)
        top.addWidget(self.element_box)
        top.addWidget(add)
        top.addWidget(save)
        layout.addLayout(top)

        hint = QLabel("Drag chips to reposition — they snap to the nearest "
                      "of nine anchors so layouts scale with any resolution.")
        hint.setObjectName("Muted")
        layout.addWidget(hint)

        self.canvas = HudCanvas(self.model)
        layout.addWidget(self.canvas, 1)
        self._load_layout()

    def reload_profiles(self) -> None:
        current = self.profile_box.currentData()
        self.profile_box.clear()
        for profile in self.store.list():
            self.profile_box.addItem(profile.name, profile.slug)
            if profile.slug == current:
                self.profile_box.setCurrentIndex(self.profile_box.count() - 1)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.reload_profiles()

    def _game_dir(self):
        slug = self.profile_box.currentData()
        if slug and self.store.exists(slug):
            return self.store.load(slug).game_dir
        return None

    def _load_layout(self) -> None:
        if not hasattr(self, "canvas"):  # combo fires while page is built
            return
        game_dir = self._game_dir()
        self.model = HudLayout.load(game_dir) if game_dir else default_layout()
        self.canvas.model = self.model
        self.canvas.update()

    def _add_element(self) -> None:
        element_type = self.element_box.currentData()
        self.model.remove(element_type)
        self.model.add(HudElement(element_type, anchor="middle_center",
                                  offset_x=0, offset_y=0))
        self.canvas.update()

    def _save(self) -> None:
        game_dir = self._game_dir()
        if game_dir is None:
            self.window.notify("Create a profile first (Home tab).", "warning")
            return
        target = self.model.save(game_dir)
        self.window.notify(f"HUD layout saved → {target}", "success")

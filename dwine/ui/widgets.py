"""Dwine's custom widgets: animated toggles, cards, toasts, stat pills."""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class ToggleSwitch(QWidget):
    """iOS-style animated toggle."""

    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self._checked = checked
        self._pos = 1.0 if checked else 0.0
        accent, track = "#4F8CFF", "#39414E"
        try:  # follow the active theme
            from ..core.config import get_config
            from ..theme.themes import load_theme

            theme = load_theme(get_config().get("theme.name", "dwine-dark"))
            accent, track = theme.color("accent"), theme.color("surface_alt")
        except Exception:
            pass
        self._accent = QColor(accent)
        self._track_off = QColor(track)
        self.setFixedSize(44, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"position", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def set_colors(self, accent: str, track_off: str) -> None:
        self._accent = QColor(accent)
        self._track_off = QColor(track_off)
        self.update()

    def get_position(self) -> float:
        return self._pos

    def set_position(self, value: float) -> None:
        self._pos = value
        self.update()

    position = Property(float, get_position, set_position)

    def isChecked(self) -> bool:  # noqa: N802 - Qt naming
        return self._checked

    def setChecked(self, checked: bool) -> None:  # noqa: N802
        if checked == self._checked:
            return
        self._checked = checked
        self._anim.stop()
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            self.toggled.emit(self._checked)
        super().mouseReleaseEvent(event)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QColor(self._track_off)
        on = QColor(self._accent)
        blend = QColor(
            int(track.red() + (on.red() - track.red()) * self._pos),
            int(track.green() + (on.green() - track.green()) * self._pos),
            int(track.blue() + (on.blue() - track.blue()) * self._pos),
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(blend)
        painter.drawRoundedRect(0, 0, 44, 24, 12, 12)
        painter.setBrush(QColor("#FFFFFF"))
        x = 3 + self._pos * (44 - 24 + 2)
        painter.drawEllipse(int(x), 3, 18, 18)


class Card(QFrame):
    """Rounded surface panel; styled by the theme QSS via #Card."""

    def __init__(self, title: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 16, 18, 16)
        self._layout.setSpacing(10)
        if title:
            label = QLabel(title)
            label.setObjectName("CardTitle")
            self._layout.addWidget(label)

    def add(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        self._layout.addLayout(layout)


class StatPill(QFrame):
    """Small labelled stat ("Ping · 23 ms")."""

    def __init__(self, label: str, value: str = "—", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 6, 12, 6)
        name = QLabel(label)
        name.setObjectName("Muted")
        self.value_label = QLabel(value)
        row.addWidget(name)
        row.addStretch(1)
        row.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class Toast(QFrame):
    """Sliding notification toast used by the notification center."""

    def __init__(self, text: str, level: str = "info", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10)
        icon = {"info": "ℹ", "success": "✓", "warning": "⚠", "error": "✕"}.get(
            level, "ℹ"
        )
        row.addWidget(QLabel(f"{icon}  {text}"))
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        self._fade = QPropertyAnimation(effect, b"opacity", self)
        self._fade.setDuration(220)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.start()
        QTimer.singleShot(4200, self._dismiss)

    def _dismiss(self) -> None:
        self._fade.setDirection(QPropertyAnimation.Direction.Backward)
        self._fade.finished.connect(self.deleteLater)
        self._fade.start()


class NotificationCenter(QWidget):
    """Stacks toasts in the window corner. Call ``notify()`` from anywhere."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 16, 16)
        self._layout.setSpacing(8)
        self._layout.addStretch(1)

    def notify(self, text: str, level: str = "info") -> None:
        self._layout.addWidget(Toast(text, level, self))
        self.reposition()

    def reposition(self) -> None:
        parent = self.parentWidget()
        if parent:
            width = 360
            self.setGeometry(
                parent.width() - width, 0, width, parent.height()
            )
            self.raise_()


class SettingRow(QWidget):
    """Label + description on the left, control on the right."""

    def __init__(
        self,
        title: str,
        description: str,
        control: QWidget,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 6, 0, 6)
        text_column = QVBoxLayout()
        name = QLabel(title)
        text_column.addWidget(name)
        if description:
            desc = QLabel(description)
            desc.setObjectName("Muted")
            desc.setWordWrap(True)
            text_column.addWidget(desc)
        row.addLayout(text_column, 1)
        row.addWidget(control, 0, Qt.AlignmentFlag.AlignRight)


class ColorButton(QFrame):
    """A small swatch that opens a color dialog when clicked."""

    changed = Signal(str)

    def __init__(self, color: str = "#FFFFFF", parent: QWidget | None = None):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(54, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Pick a color")

    def color(self) -> str:
        return self._color.name().upper()

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            from PySide6.QtWidgets import QColorDialog

            picked = QColorDialog.getColor(self._color, self, "Pick a color")
            if picked.isValid():
                self._color = picked
                self.update()
                self.changed.emit(self.color())
        super().mouseReleaseEvent(event)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self._color)
        painter.setPen(QPen(QColor("#5A6472"), 1))
        painter.drawRoundedRect(1, 1, 52, 24, 6, 6)


class ColorSwatch(QFrame):
    """Clickable color square used by the crosshair/theme editors."""

    clicked = Signal(str)

    def __init__(self, color: str, selected: bool = False, parent=None):
        super().__init__(parent)
        self.color = color
        self.selected = selected
        self.setFixedSize(26, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.color)
        super().mouseReleaseEvent(event)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(self.color))
        pen = QPen(QColor("#FFFFFF" if self.selected else "#00000000"), 2)
        painter.setPen(pen)
        painter.drawRoundedRect(2, 2, 22, 22, 6, 6)

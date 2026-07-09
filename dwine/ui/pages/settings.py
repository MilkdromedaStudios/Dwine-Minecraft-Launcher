"""Settings: launcher theme, game memory, Java path, auto-clean."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ...core.config import get_config
from ...theme.themes import list_themes, load_theme
from ..widgets import Card, SettingRow, ToggleSwitch


class SettingsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        cfg = get_config()

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)
        scroll.setWidget(inner)

        # -- appearance ---------------------------------------------------
        appearance = Card("Appearance")
        theme_box = QComboBox()
        current = cfg.get("theme.name", "dwine-dark")
        for name in list_themes():
            theme_box.addItem(load_theme(name).display_name, name)
            if name == current:
                theme_box.setCurrentIndex(theme_box.count() - 1)

        def change_theme(_index: int) -> None:
            cfg.set("theme.name", theme_box.currentData())
            self.window.apply_theme()
            self.window.notify(f"Theme: {theme_box.currentText()}", "success")

        theme_box.currentIndexChanged.connect(change_theme)
        appearance.add(SettingRow("Theme", "Launcher color scheme.", theme_box))
        layout.addWidget(appearance)

        # -- game -------------------------------------------------------------
        game = Card("Game")
        memory_row = QHBoxLayout()
        memory = QSlider(Qt.Orientation.Horizontal)
        memory.setRange(1024, 16384)
        memory.setSingleStep(512)
        memory.setValue(int(cfg.get("game.memory_mb", 4096)))
        memory_label = QLabel(f"{memory.value()} MB")
        memory.valueChanged.connect(
            lambda v: memory_label.setText(f"{v} MB"))
        memory.sliderReleased.connect(
            lambda: cfg.set("game.memory_mb", memory.value()))
        memory_row.addWidget(memory, 1)
        memory_row.addWidget(memory_label)
        holder = QWidget()
        holder.setLayout(memory_row)
        game.add(SettingRow("Memory", "RAM given to the game (Xmx).", holder))

        java_edit = QLineEdit(cfg.get("game.java_path", ""))
        java_edit.setPlaceholderText("auto (Dwine manages Java for you)")
        java_edit.editingFinished.connect(
            lambda: cfg.set("game.java_path", java_edit.text().strip()))
        game.add(SettingRow("Java path", "Leave empty for the managed runtime.",
                            java_edit))

        auto_clean = ToggleSwitch(cfg.get("performance.auto_clean.enabled", True))
        auto_clean.toggled.connect(
            lambda s: cfg.set("performance.auto_clean.enabled", s))
        game.add(SettingRow(
            "Auto-clean", "Sweep old logs/crash reports and trim the download "
            "cache before each launch.", auto_clean))
        layout.addWidget(game)

        layout.addStretch(1)

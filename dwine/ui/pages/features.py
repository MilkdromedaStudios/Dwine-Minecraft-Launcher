"""Features: 100+ client toggles, each with its own settings.

Every feature row expands into its settings — sliders, colors, choices —
generated straight from the catalog metadata in
:mod:`dwine.features.registry`. Everything is saved to ``settings.json``
and written into the profile's game directory at launch, where the Dwine
companion mod renders it **in game** (including the in-game HUD editor).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...core.config import get_config
from ...features import registry
from ...features.registry import FLAG_INPUT_AUTOMATION, FLAG_RADAR_LIKE, Setting
from ..widgets import Card, ColorButton, ToggleSwitch

CATEGORY_LABELS = {
    "performance": "Performance",
    "hud": "HUD",
    "visual": "Visual",
    "chat": "Chat",
    "interface": "Interface",
    "utility": "Utility",
    "hypixel": "Hypixel",
    "media": "Media",
}


def _setting_editor(feature_id: str, setting: Setting, value) -> QWidget:
    """Build the right control for a setting and wire it to the config."""
    cfg = get_config()
    key = f"features.{feature_id}.settings.{setting.id}"

    if setting.kind == "toggle":
        toggle = ToggleSwitch(checked=bool(value))
        toggle.toggled.connect(lambda state: cfg.set(key, state))
        return toggle

    if setting.kind == "slider":
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(setting.minimum, setting.maximum)
        slider.setSingleStep(setting.step)
        slider.setPageStep(setting.step)
        slider.setValue(int(value))
        slider.setMinimumWidth(140)
        label = QLabel(f"{int(value)}{setting.suffix}")
        label.setMinimumWidth(64)
        label.setAlignment(Qt.AlignmentFlag.AlignRight
                           | Qt.AlignmentFlag.AlignVCenter)
        slider.valueChanged.connect(
            lambda v: label.setText(f"{v}{setting.suffix}"))
        slider.sliderReleased.connect(lambda: cfg.set(key, slider.value()))
        # also save on keyboard/scroll changes once the value settles
        slider.valueChanged.connect(
            lambda v: None if slider.isSliderDown() else cfg.set(key, v))
        row.addWidget(slider, 1)
        row.addWidget(label)
        return holder

    if setting.kind == "color":
        button = ColorButton(str(value))
        button.changed.connect(lambda color: cfg.set(key, color))
        return button

    if setting.kind == "choice":
        box = QComboBox()
        for choice in setting.choices:
            box.addItem(choice.replace("_", " "), choice)
            if choice == value:
                box.setCurrentIndex(box.count() - 1)
        box.currentIndexChanged.connect(
            lambda _i: cfg.set(key, box.currentData()))
        return box

    edit = QLineEdit(str(value))
    edit.setMaximumWidth(220)
    edit.editingFinished.connect(lambda: cfg.set(key, edit.text()))
    return edit


class FeatureRow(QWidget):
    """Header (name/description/toggle) + collapsible settings body."""

    def __init__(self, feature, enabled: bool, window):
        super().__init__()
        self.feature = feature
        self.window = window

        column = QVBoxLayout(self)
        column.setContentsMargins(0, 6, 0, 6)
        column.setSpacing(4)

        header = QHBoxLayout()
        text_column = QVBoxLayout()
        name = QLabel(feature.name)
        text_column.addWidget(name)
        description = feature.description
        if FLAG_INPUT_AUTOMATION in feature.flags:
            description += "  🔒 singleplayer only — enforced"
        elif FLAG_RADAR_LIKE in feature.flags:
            description += "  🛡 fair-play handling on competitive servers"
        desc = QLabel(description)
        desc.setObjectName("Muted")
        desc.setWordWrap(True)
        text_column.addWidget(desc)
        header.addLayout(text_column, 1)

        if feature.settings or feature.id == "custom_crosshair":
            self.expand_button = QPushButton("⚙")
            self.expand_button.setFixedWidth(34)
            self.expand_button.setCheckable(True)
            self.expand_button.setToolTip("Feature settings")
            self.expand_button.toggled.connect(self._toggle_body)
            header.addWidget(self.expand_button, 0)

        toggle = ToggleSwitch(checked=enabled)
        toggle.toggled.connect(self._set_enabled)
        header.addWidget(toggle, 0, Qt.AlignmentFlag.AlignRight)
        column.addLayout(header)

        self.body = QWidget()
        self.body.setVisible(False)
        body_layout = QVBoxLayout(self.body)
        body_layout.setContentsMargins(18, 2, 8, 4)
        body_layout.setSpacing(6)
        column.addWidget(self.body)
        self._body_built = False

    def _build_body(self) -> None:
        if self._body_built:
            return
        self._body_built = True
        cfg = get_config()
        values = registry.feature_settings(cfg, self.feature.id)
        body_layout = self.body.layout()
        for setting in self.feature.settings:
            row = QHBoxLayout()
            label = QLabel(setting.label)
            label.setObjectName("Muted")
            row.addWidget(label, 1)
            row.addWidget(
                _setting_editor(self.feature.id, setting,
                                values.get(setting.id, setting.default)),
                0, Qt.AlignmentFlag.AlignRight)
            body_layout.addLayout(row)

        if self.feature.id == "custom_crosshair":
            drawpad = QPushButton("Open crosshair drawpad …")
            drawpad.clicked.connect(self._open_drawpad)
            body_layout.addWidget(drawpad, 0, Qt.AlignmentFlag.AlignLeft)

    def _toggle_body(self, expanded: bool) -> None:
        if expanded:
            self._build_body()
        self.body.setVisible(expanded)

    def _open_drawpad(self) -> None:
        from ..crosshair_pad import CrosshairDrawpadDialog

        if CrosshairDrawpadDialog(self).exec() == QDialog.DialogCode.Accepted:
            self.window.notify(
                "Custom crosshair saved — it renders into the theme pack "
                "on next launch.", "success")

    def _set_enabled(self, state: bool) -> None:
        get_config().set(f"features.{self.feature.id}.enabled", state)
        self.window.notify(
            f"{self.feature.name}: {'on' if state else 'off'} "
            "(applies on next launch)")


class FeaturesPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)

        banner = QLabel(
            f"{len(registry.FEATURES)} built-in features, every one with its "
            "own settings (the ⚙ button). All of it is rendered in game by "
            "the companion mod — the launcher just holds the remote. "
            "Restricted features are enforced off on multiplayer "
            "automatically; that part is not a setting."
        )
        banner.setObjectName("Muted")
        banner.setWordWrap(True)
        layout.addWidget(banner)

        tabs = QTabWidget()
        for category in registry.CATEGORIES:
            tabs.addTab(self._category_tab(category),
                        CATEGORY_LABELS.get(category, category.title()))
        layout.addWidget(tabs, 1)

    def _category_tab(self, category: str) -> QWidget:
        cfg = get_config()
        enabled = registry.enabled_features(cfg)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(4, 12, 4, 12)
        layout.setSpacing(10)

        card = Card()
        for feature in registry.by_category(category):
            card.add(FeatureRow(feature, enabled.get(feature.id, False),
                                self.window))
        layout.addWidget(card)
        layout.addStretch(1)
        scroll.setWidget(inner)
        return scroll

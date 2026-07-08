"""Features: every Dwine toggle, grouped by category, with safety badges."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...core.config import get_config
from ...features import registry
from ...features.registry import FLAG_INPUT_AUTOMATION, FLAG_RADAR_LIKE
from ..widgets import Card, SettingRow, ToggleSwitch

CATEGORY_LABELS = {
    "performance": "Performance",
    "hud": "HUD",
    "visual": "Visual",
    "utility": "Utility",
    "hypixel": "Hypixel",
    "media": "Media",
}


class FeaturesPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)

        banner = QLabel(
            "Every feature is cosmetic or quality-of-life. Restricted "
            "features are enforced off on multiplayer automatically — that "
            "part is not a setting."
        )
        banner.setObjectName("Muted")
        banner.setWordWrap(True)
        layout.addWidget(banner)

        tabs = QTabWidget()
        for category in registry.CATEGORIES:
            tabs.addTab(self._category_tab(category), CATEGORY_LABELS[category])
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
            toggle = ToggleSwitch(checked=enabled.get(feature.id, False))
            toggle.toggled.connect(
                lambda state, fid=feature.id: self._set_feature(fid, state)
            )
            description = feature.description
            if FLAG_INPUT_AUTOMATION in feature.flags:
                description += "  🔒 singleplayer only — enforced"
            elif FLAG_RADAR_LIKE in feature.flags:
                description += "  🛡 fair-play variant on competitive servers"
            card.add(SettingRow(feature.name, description, toggle))
        layout.addWidget(card)
        layout.addStretch(1)
        scroll.setWidget(inner)
        return scroll

    def _set_feature(self, feature_id: str, state: bool) -> None:
        get_config().set(f"features.{feature_id}.enabled", state)
        self.window.notify(
            f"{registry.get(feature_id).name}: {'on' if state else 'off'} "
            "(applies on next launch)"
        )

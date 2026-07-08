"""News & patch notes."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel,
    QScrollArea,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ...launcher.news import fetch_news, patch_notes
from ..widgets import Card


class NewsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)

        tabs = QTabWidget()

        # -- news tab -----------------------------------------------------
        news_scroll = QScrollArea()
        news_scroll.setWidgetResizable(True)
        news_inner = QWidget()
        self.news_layout = QVBoxLayout(news_inner)
        self.news_layout.setContentsMargins(4, 12, 4, 12)
        self.news_layout.setSpacing(10)
        news_scroll.setWidget(news_inner)
        tabs.addTab(news_scroll, "News")

        # -- patch notes tab ---------------------------------------------
        notes = QTextBrowser()
        notes.setMarkdown(patch_notes())
        notes.setOpenExternalLinks(True)
        tabs.addTab(notes, "Patch notes")

        layout.addWidget(tabs)
        window.run_async(fetch_news, on_done=self._show)

    def _show(self, items) -> None:
        for item in items:
            card = Card(item.title)
            body = QLabel(item.body)
            body.setWordWrap(True)
            card.add(body)
            meta = QLabel(f"{item.date} · {item.tag}")
            meta.setObjectName("Muted")
            card.add(meta)
            self.news_layout.addWidget(card)
        self.news_layout.addStretch(1)

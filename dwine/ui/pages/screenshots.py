"""Screenshot gallery: thumbnails across all profiles, quick actions."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...launcher.profiles import ProfileStore
from ...tools import screenshots as shots


class ScreenshotsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.store = ProfileStore()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)

        top = QHBoxLayout()
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.reload)
        collect = QPushButton("Collect from profiles")
        collect.clicked.connect(self._collect)
        open_folder = QPushButton("Open folder")
        open_folder.clicked.connect(self._open_folder)
        top.addWidget(refresh)
        top.addWidget(collect)
        top.addWidget(open_folder)
        top.addStretch(1)
        layout.addLayout(top)

        self.grid = QListWidget()
        self.grid.setViewMode(QListView.ViewMode.IconMode)
        self.grid.setIconSize(QSize(192, 108))
        self.grid.setResizeMode(QListView.ResizeMode.Adjust)
        self.grid.setSpacing(10)
        layout.addWidget(self.grid, 1)

        self.empty = QLabel("No screenshots yet — press F2 in game!")
        self.empty.setObjectName("Muted")
        layout.addWidget(self.empty)
        self.reload()

    def reload(self) -> None:
        self.grid.clear()
        gallery = shots.gallery(self.store.list())
        self.empty.setVisible(not gallery)
        for shot in gallery[:200]:
            pixmap = QPixmap(str(shot.path))
            if pixmap.isNull():
                continue
            icon = QIcon(pixmap.scaled(
                192, 108,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation))
            item = QListWidgetItem(icon, f"{shot.profile}\n{shot.name}")
            item.setData(Qt.ItemDataRole.UserRole, str(shot.path))
            self.grid.addItem(item)

    def _collect(self) -> None:
        copied = shots.collect(self.store.list())
        self.window.notify(f"Collected {copied} screenshot(s)", "success")
        self.reload()

    def _open_folder(self) -> None:
        import webbrowser

        from ...core import paths

        webbrowser.open(paths.screenshots_dir().as_uri())

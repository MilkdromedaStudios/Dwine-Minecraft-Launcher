"""The Dwine launcher window: sidebar navigation, themed pages, toasts."""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .. import __app_name__, __version__
from ..core import paths
from ..core.config import get_config
from ..core.events import bus
from ..core.log import setup as setup_logging
from ..integrations.discord_rpc import RichPresence
from ..plugins.loader import load_all as load_plugins
from ..theme.engine import background_css, build_qss
from ..theme.themes import load_theme
from .widgets import NotificationCenter

PAGES = [
    ("home", "⌂  Home"),
    ("mods", "▤  Mods && Packs"),
    ("features", "✦  Features"),
    ("hud", "▦  HUD Editor"),
    ("screenshots", "◨  Screenshots"),
    ("news", "☰  News"),
    ("logs", "≣  Logs"),
    ("accounts", "◉  Accounts"),
    ("settings", "⚙  Settings"),
]


class Worker(QObject):
    """Run a callable on a QThread; report result or error back to the UI."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn, self._args, self._kwargs = fn, args, kwargs

    def run(self) -> None:
        try:
            self.finished.emit(self._fn(*self._args, **self._kwargs))
        except Exception as exc:  # noqa: BLE001 - surfaced as a toast
            self.failed.emit(str(exc))


class DwineWindow(QMainWindow):
    event_received = Signal(str, dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__app_name__} · {__version__}")
        self.resize(1180, 720)
        self.setMinimumSize(960, 600)
        self._threads: list[QThread] = []

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # -- sidebar ----------------------------------------------------
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(216)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(10, 6, 10, 14)
        side_layout.setSpacing(2)

        logo = QLabel("◆ DWINE")
        logo.setObjectName("Logo")
        side_layout.addWidget(logo)

        self._nav = QButtonGroup(self)
        self._nav.setExclusive(True)
        self.stack = QStackedWidget()
        self._page_index: dict[str, int] = {}

        for page_id, label in PAGES:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self._nav.addButton(button)
            side_layout.addWidget(button)
            index = self.stack.addWidget(self._build_page(page_id))
            self._page_index[page_id] = index
            button.clicked.connect(
                lambda _checked=False, i=index: self.stack.setCurrentIndex(i)
            )

        side_layout.addStretch(1)
        version = QLabel(f"v{__version__} · 100% legit")
        version.setObjectName("Muted")
        side_layout.addWidget(version)

        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)

        self._nav.buttons()[0].setChecked(True)
        self.notifications = NotificationCenter(self)

        # Launcher-core events arrive from worker threads; hop to the UI
        # thread through a queued signal before touching widgets.
        self.event_received.connect(self._on_event)
        bus.on("notify", lambda e, p: self.event_received.emit(e, p))
        bus.on("safety.enforced", lambda e, p: self.event_received.emit(e, p))
        bus.on("game.exited", lambda e, p: self.event_received.emit(e, p))

        self._plugins = load_plugins()
        for plugin in self._plugins:
            for title, factory in plugin.api.ui_pages:
                try:
                    self.stack.addWidget(factory(self))
                except Exception:
                    pass

        self.rpc = RichPresence()
        self.rpc.connect()
        self.apply_theme()
        self._start_auto_update_check()

    # ------------------------------------------------------------------

    def _build_page(self, page_id: str) -> QWidget:
        from .pages import build

        return build(page_id, self)

    def apply_theme(self) -> None:
        theme = load_theme(get_config().get("theme.name", "dwine-dark"))
        app = QApplication.instance()
        if app:
            app.setStyleSheet(
                build_qss(theme)
                + f"\nQStackedWidget > QWidget {{ {background_css(theme)} }}"
            )
        bus.emit("theme.changed", {"name": theme.name})

    def notify(self, text: str, level: str = "info") -> None:
        self.notifications.notify(text, level)

    def _start_auto_update_check(self) -> None:
        if not get_config().get("launcher.auto_update", True):
            return

        def done(info) -> None:
            if info.available:
                self.notify(
                    f"Dwine update available: {info.current} → {info.latest}. "
                    "Run `dwine update` to install it.",
                    "info",
                )

        from ..launcher import update

        self.run_async(update.check, on_done=done, on_error=lambda _msg: None)

    def run_async(self, fn, on_done=None, on_error=None, *args, **kwargs) -> None:
        thread = QThread(self)
        worker = Worker(fn, *args, **kwargs)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(lambda result: on_done(result) if on_done else None)
        worker.failed.connect(
            lambda msg: (on_error or (lambda m: self.notify(m, "error")))(msg)
        )
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._threads.remove(thread))
        self._threads.append(thread)
        thread.start()

    def _on_event(self, event: str, payload: dict) -> None:
        if event == "notify":
            self.notify(payload.get("text", ""), payload.get("level", "info"))
        elif event == "safety.enforced":
            self.notify(
                f"Safety policy: {payload.get('feature')} — {payload.get('reason')}",
                "warning",
            )
        elif event == "game.exited":
            code = payload.get("code", 0)
            level = "success" if code == 0 else "warning"
            self.notify(f"Game exited (code {code})", level)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.notifications.reposition()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.rpc.close()
        for thread in list(self._threads):
            thread.quit()
            thread.wait(3000)
        super().closeEvent(event)


def main() -> int:
    setup_logging()
    paths.ensure_tree()
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setWindowIcon(QIcon())
    window = DwineWindow()
    window.show()
    return app.exec()

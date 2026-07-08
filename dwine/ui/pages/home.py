"""Home: profile picker, version info, quick-join, and the Play button."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...launcher.accounts import AccountStore
from ...launcher.news import fetch_news
from ...launcher.profiles import BUILTIN_PRESETS, Profile, ProfileStore
from ..widgets import Card


class HomePage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.store = ProfileStore()
        self.accounts = AccountStore()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        title = QLabel("Ready to play")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        # -- launch card -------------------------------------------------
        launch_card = Card()
        row = QHBoxLayout()
        row.setSpacing(12)

        self.profile_box = QComboBox()
        self.profile_box.setMinimumWidth(220)
        self.reload_profiles()

        new_button = QPushButton("+ New profile")
        new_button.clicked.connect(self.create_profile)

        self.server_edit = QLineEdit()
        self.server_edit.setPlaceholderText("Quick join server (optional) …")

        play = QPushButton("PLAY")
        play.setObjectName("Play")
        play.setCursor(Qt.CursorShape.PointingHandCursor)
        play.clicked.connect(self.play)

        row.addWidget(self.profile_box, 2)
        row.addWidget(new_button, 0)
        row.addWidget(self.server_edit, 2)
        row.addWidget(play, 0)
        launch_card.add_layout(row)

        self.status = QLabel("")
        self.status.setObjectName("Muted")
        launch_card.add(self.status)
        layout.addWidget(launch_card)

        # -- news --------------------------------------------------------
        news_card = Card("News")
        self.news_box = QVBoxLayout()
        news_card.add_layout(self.news_box)
        layout.addWidget(news_card)
        layout.addStretch(1)
        self.window.run_async(fetch_news, on_done=self._show_news)

    # ------------------------------------------------------------------

    def reload_profiles(self) -> None:
        self.profile_box.clear()
        profiles = self.store.list()
        if not profiles:
            self.profile_box.addItem("Latest release (auto)", None)
        for profile in profiles:
            label = f"{profile.name} · {profile.version or 'latest'} · {profile.loader}"
            self.profile_box.addItem(label, profile.slug)

    def create_profile(self) -> None:
        # Create the four builtin presets in one click if none exist yet.
        created = []
        for preset in BUILTIN_PRESETS:
            spec = BUILTIN_PRESETS[preset]
            if not self.store.exists(spec["display_name"]):
                self.store.create_from_preset(preset, version="")
                created.append(spec["display_name"])
        self.reload_profiles()
        self.window.notify(
            f"Created profiles: {', '.join(created)}" if created
            else "All starter profiles already exist", "success" if created else "info",
        )

    def _selected_profile(self) -> Profile:
        slug = self.profile_box.currentData()
        if slug:
            return self.store.load(slug)
        profile = Profile(name="Default", version="", loader="vanilla")
        self.store.save(profile)
        return profile

    def play(self) -> None:
        from ...launcher.play import launch_profile

        profile = self._selected_profile()
        account = self.accounts.active()
        if account is None:
            self.window.notify(
                "No account yet — add one in the Accounts tab.", "warning"
            )
            return
        server = self.server_edit.text().strip() or None
        self.status.setText(f"Preparing {profile.name} …")

        def do_launch():
            return launch_profile(profile, account, server=server)

        def done(_proc):
            self.status.setText(f"{profile.name} is running.")
            self.window.notify("Game launched — have fun!", "success")

        self.window.run_async(do_launch, on_done=done,
                              on_error=lambda m: self.status.setText(m))

    def _show_news(self, items) -> None:
        for item in items[:4]:
            label = QLabel(f"<b>{item.title}</b><br>{item.body}")
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.RichText)
            self.news_box.addWidget(label)

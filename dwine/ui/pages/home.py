"""Home: profile picker, the version chooser, quick-join, and Play.

The version chooser lists every Minecraft version from Mojang's official
manifest — releases by default, snapshots and old beta/alpha on demand —
plus a loader picker (Vanilla / Fabric / Quilt / Forge). Changes apply to
the selected profile immediately.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core.config import get_config
from ...launcher.accounts import AccountStore
from ...launcher.profiles import Profile, ProfileStore
from ..widgets import Card

LOADERS = ("vanilla", "fabric", "quilt", "forge")


def _fetch_version_ids(snapshots: bool, old_versions: bool) -> list[str]:
    from ...launcher import manifest

    versions = manifest.list_versions(
        releases=True, snapshots=snapshots, old_versions=old_versions
    )
    return [v.id for v in versions]


class NewProfileDialog(QDialog):
    """Name + version + loader — that's a profile. No presets."""

    def __init__(self, parent, version_ids: list[str]):
        super().__init__(parent)
        self.setWindowTitle("New profile")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Profile name …")
        layout.addWidget(QLabel("Name"))
        layout.addWidget(self.name_edit)

        self.version_box = QComboBox()
        self.version_box.addItem("Latest release", "")
        for version_id in version_ids:
            self.version_box.addItem(version_id, version_id)
        layout.addWidget(QLabel("Minecraft version"))
        layout.addWidget(self.version_box)

        self.loader_box = QComboBox()
        for loader in LOADERS:
            self.loader_box.addItem(loader.capitalize(), loader)
        self.loader_box.setCurrentIndex(1)  # fabric: what the companion mod uses
        layout.addWidget(QLabel("Mod loader"))
        layout.addWidget(self.loader_box)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def result_profile(self) -> Profile | None:
        name = self.name_edit.text().strip()
        if not name:
            return None
        return Profile(
            name=name,
            version=self.version_box.currentData() or "",
            loader=self.loader_box.currentData(),
        )


class HomePage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.store = ProfileStore()
        self.store.ensure_default()
        self._version_ids: list[str] = []
        self._loading_profile = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        title = QLabel("Ready to play")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        # -- launch card -------------------------------------------------
        launch_card = Card()

        profile_row = QHBoxLayout()
        profile_row.setSpacing(12)
        profile_row.addWidget(QLabel("Profile:"))
        self.profile_box = QComboBox()
        self.profile_box.setMinimumWidth(220)
        self.profile_box.currentIndexChanged.connect(self._profile_selected)
        profile_row.addWidget(self.profile_box, 2)
        new_button = QPushButton("+ New profile")
        new_button.clicked.connect(self.create_profile)
        profile_row.addWidget(new_button, 0)
        delete_button = QPushButton("Delete")
        delete_button.setObjectName("Danger")
        delete_button.clicked.connect(self.delete_profile)
        profile_row.addWidget(delete_button, 0)
        launch_card.add_layout(profile_row)

        # -- version chooser ----------------------------------------------
        version_row = QHBoxLayout()
        version_row.setSpacing(12)
        version_row.addWidget(QLabel("Version:"))
        self.version_box = QComboBox()
        self.version_box.setMinimumWidth(160)
        self.version_box.addItem("Latest release", "")  # usable pre-fetch
        self.version_box.currentIndexChanged.connect(self._version_changed)
        version_row.addWidget(self.version_box, 2)

        version_row.addWidget(QLabel("Loader:"))
        self.loader_box = QComboBox()
        for loader in LOADERS:
            self.loader_box.addItem(loader.capitalize(), loader)
        self.loader_box.currentIndexChanged.connect(self._loader_changed)
        version_row.addWidget(self.loader_box, 1)

        cfg = get_config()
        self.snapshots_check = QCheckBox("Snapshots")
        self.snapshots_check.setChecked(bool(cfg.get("launcher.show_snapshots", False)))
        self.snapshots_check.toggled.connect(self._version_filters_changed)
        version_row.addWidget(self.snapshots_check)

        self.old_check = QCheckBox("Beta/Alpha")
        self.old_check.setChecked(bool(cfg.get("launcher.show_old_versions", False)))
        self.old_check.toggled.connect(self._version_filters_changed)
        version_row.addWidget(self.old_check)
        launch_card.add_layout(version_row)

        play_row = QHBoxLayout()
        play_row.setSpacing(12)
        self.server_edit = QLineEdit()
        self.server_edit.setPlaceholderText("Quick join server (optional) …")
        play = QPushButton("PLAY")
        play.setObjectName("Play")
        play.setCursor(Qt.CursorShape.PointingHandCursor)
        play.clicked.connect(self.play)
        play_row.addWidget(self.server_edit, 2)
        play_row.addWidget(play, 0)
        launch_card.add_layout(play_row)

        self.status = QLabel("")
        self.status.setObjectName("Muted")
        launch_card.add(self.status)
        layout.addWidget(launch_card)

        layout.addStretch(1)

        self.reload_profiles()
        self._refresh_versions()

    # -- profiles ------------------------------------------------------

    def reload_profiles(self) -> None:
        self._loading_profile = True
        current = self.profile_box.currentData()
        self.profile_box.clear()
        for profile in self.store.list():
            label = f"{profile.name} · {profile.version or 'latest'} · {profile.loader}"
            self.profile_box.addItem(label, profile.slug)
            if profile.slug == current:
                self.profile_box.setCurrentIndex(self.profile_box.count() - 1)
        self._loading_profile = False
        self._profile_selected()

    def create_profile(self) -> None:
        dialog = NewProfileDialog(self, self._version_ids)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        profile = dialog.result_profile()
        if profile is None:
            self.window.notify("Give the profile a name.", "warning")
            return
        if self.store.exists(profile.name):
            self.window.notify(f"Profile '{profile.name}' already exists.", "warning")
            return
        self.store.save(profile)
        self.reload_profiles()
        self.profile_box.setCurrentIndex(
            self.profile_box.findData(profile.slug))
        self.window.notify(f"Created profile: {profile.name}", "success")

    def delete_profile(self) -> None:
        slug = self.profile_box.currentData()
        if not slug:
            return
        if self.profile_box.count() <= 1:
            self.window.notify("You need at least one profile.", "warning")
            return
        self.store.delete(slug)
        self.reload_profiles()
        self.window.notify("Profile deleted (its worlds/config were kept).", "info")

    def _selected_profile(self) -> Profile:
        slug = self.profile_box.currentData()
        if slug and self.store.exists(slug):
            return self.store.load(slug)
        return self.store.ensure_default()

    def _profile_selected(self) -> None:
        if self._loading_profile:
            return
        profile = self._selected_profile()
        self._loading_profile = True
        index = self.version_box.findData(profile.version or "")
        self.version_box.setCurrentIndex(index if index >= 0 else 0)
        loader_index = self.loader_box.findData(profile.loader)
        if loader_index >= 0:
            self.loader_box.setCurrentIndex(loader_index)
        self._loading_profile = False

    # -- version chooser -------------------------------------------------

    def _refresh_versions(self) -> None:
        snapshots = self.snapshots_check.isChecked()
        old_versions = self.old_check.isChecked()

        def done(version_ids: list[str]) -> None:
            self._version_ids = version_ids
            self._populate_version_box()

        def failed(_msg: str) -> None:
            self.status.setText(
                "Couldn't fetch the version list (offline?) — "
                "'Latest release' still works.")

        self.window.run_async(
            lambda: _fetch_version_ids(snapshots, old_versions),
            on_done=done, on_error=failed,
        )

    def _populate_version_box(self) -> None:
        self._loading_profile = True
        self.version_box.clear()
        self.version_box.addItem("Latest release", "")
        for version_id in self._version_ids:
            self.version_box.addItem(version_id, version_id)
        self._loading_profile = False
        self._profile_selected()

    def _version_filters_changed(self) -> None:
        cfg = get_config()
        cfg.set("launcher.show_snapshots", self.snapshots_check.isChecked())
        cfg.set("launcher.show_old_versions", self.old_check.isChecked())
        self._refresh_versions()

    def _version_changed(self) -> None:
        if self._loading_profile:
            return
        profile = self._selected_profile()
        profile.version = self.version_box.currentData() or ""
        self.store.save(profile)
        self._update_profile_label(profile)

    def _loader_changed(self) -> None:
        if self._loading_profile:
            return
        profile = self._selected_profile()
        profile.loader = self.loader_box.currentData()
        self.store.save(profile)
        self._update_profile_label(profile)

    def _update_profile_label(self, profile: Profile) -> None:
        index = self.profile_box.findData(profile.slug)
        if index >= 0:
            self.profile_box.setItemText(
                index,
                f"{profile.name} · {profile.version or 'latest'} · {profile.loader}",
            )

    def showEvent(self, event) -> None:  # noqa: N802 - pick up CLI-made profiles
        super().showEvent(event)
        self.reload_profiles()

    # -- play ------------------------------------------------------------

    def play(self) -> None:
        from ...launcher.play import launch_profile

        profile = self._selected_profile()
        server = self.server_edit.text().strip() or None
        self.status.setText(f"Preparing {profile.name} …")

        def do_launch():
            # Fresh store: sees accounts added since startup; the token
            # refresh (network) also belongs here, off the UI thread.
            account = AccountStore().active()
            if account is None:
                raise RuntimeError(
                    "No account yet — add one in the Accounts tab.")
            return launch_profile(profile, account, server=server)

        def done(_proc):
            self.status.setText(f"{profile.name} is running.")
            self.window.notify("Game launched — have fun!", "success")

        def failed(message: str) -> None:
            self.status.setText(message)
            self.window.notify(message, "error")

        self.window.run_async(do_launch, on_done=done, on_error=failed)

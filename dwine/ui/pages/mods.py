"""Mods & Packs: Modrinth search, one-click installs, updates.

Everything installs from Modrinth's official API with sha512
verification. The profile list refreshes every time the page is shown,
so profiles created on Home (or from the CLI) appear immediately.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...content import modrinth
from ...content.mods import ModManager
from ...content.resourcepacks import ResourcePackManager
from ...content.shaders import ShaderManager
from ...launcher.profiles import ProfileStore


class ModsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.store = ProfileStore()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        top = QHBoxLayout()
        top.addWidget(QLabel("Profile:"))
        self.profile_box = QComboBox()
        top.addWidget(self.profile_box, 1)
        self.reload_profiles()
        layout.addLayout(top)

        tabs = QTabWidget()
        tabs.addTab(self._content_tab("mod"), "Mods")
        tabs.addTab(self._content_tab("resourcepack"), "Resource Packs")
        tabs.addTab(self._content_tab("shader"), "Shaders")
        layout.addWidget(tabs, 1)

    # ------------------------------------------------------------------

    def reload_profiles(self) -> None:
        current = self.profile_box.currentData()
        self.profile_box.clear()
        for profile in self.store.list():
            label = f"{profile.name} · {profile.version or 'latest'} · {profile.loader}"
            self.profile_box.addItem(label, profile.slug)
            if profile.slug == current:
                self.profile_box.setCurrentIndex(self.profile_box.count() - 1)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.reload_profiles()

    def _profile(self):
        slug = self.profile_box.currentData()
        if slug and self.store.exists(slug):
            return self.store.load(slug)
        # Never dead-end the page: fall back to (or create) a default.
        profile = self.store.ensure_default()
        self.reload_profiles()
        return profile

    def _manager(self, kind: str, profile):
        if kind == "mod":
            return ModManager(profile)
        if kind == "resourcepack":
            return ResourcePackManager(profile)
        return ShaderManager(profile)

    def _content_tab(self, kind: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 12, 0, 0)

        search_row = QHBoxLayout()
        search = QLineEdit()
        search.setPlaceholderText(f"Search Modrinth {kind}s …")
        results = QListWidget()
        results.setWordWrap(True)
        button = QPushButton("Search")
        status = QLabel("")
        status.setObjectName("Muted")

        def run_search() -> None:
            query = search.text().strip()
            try:
                profile = self._profile()
            except Exception as exc:  # noqa: BLE001 - surface, don't crash the slot
                self.window.notify(str(exc), "error")
                return
            status.setText("Searching Modrinth …")
            button.setEnabled(False)

            def do():
                return modrinth.search(
                    query,
                    project_type=kind,
                    game_version=profile.version or None,
                    loader=profile.loader if kind == "mod" and
                    profile.loader != "vanilla" else None,
                )

            def done(hits):
                button.setEnabled(True)
                results.clear()
                if not hits:
                    status.setText(
                        f"No {kind}s found for '{query}' on "
                        f"{profile.version or 'latest'} ({profile.loader}).")
                    return
                status.setText(f"{len(hits)} result(s) — double-click or "
                               "select + Install.")
                for hit in hits:
                    item = QListWidgetItem(
                        f"{hit.title}  ·  {hit.downloads:,} downloads\n"
                        f"    {hit.description[:110]}"
                    )
                    item.setData(Qt.ItemDataRole.UserRole, hit.slug)
                    results.addItem(item)

            def failed(message: str) -> None:
                button.setEnabled(True)
                status.setText("Search failed — check your connection.")
                self.window.notify(f"Modrinth search failed: {message}", "error")

            self.window.run_async(do, on_done=done, on_error=failed)

        button.clicked.connect(run_search)
        search.returnPressed.connect(run_search)
        search_row.addWidget(search, 1)
        search_row.addWidget(button)
        layout.addLayout(search_row)
        layout.addWidget(status)
        layout.addWidget(results, 1)

        actions = QHBoxLayout()
        install = QPushButton("Install selected")
        install.setObjectName("Primary")

        def do_install() -> None:
            item = results.currentItem()
            if not item:
                self.window.notify("Select a search result first.", "info")
                return
            slug = item.data(Qt.ItemDataRole.UserRole)
            try:
                profile = self._profile()
            except Exception as exc:  # noqa: BLE001
                self.window.notify(str(exc), "error")
                return
            if kind == "mod" and profile.loader == "vanilla":
                self.window.notify(
                    "Mods need a loader — switch this profile to Fabric, "
                    "Quilt or Forge on the Home tab.", "warning")
                return
            manager = self._manager(kind, profile)
            install.setEnabled(False)

            def done(_result) -> None:
                install.setEnabled(True)
                self.window.notify(
                    f"Installed {slug} into {profile.name}", "success")

            def failed(message: str) -> None:
                install.setEnabled(True)
                self.window.notify(f"Install failed: {message}", "error")

            self.window.run_async(lambda: manager.install(slug),
                                  on_done=done, on_error=failed)

        install.clicked.connect(do_install)
        results.itemDoubleClicked.connect(lambda _item: do_install())
        actions.addWidget(install)

        if kind == "mod":
            update_all = QPushButton("Update all")

            def do_update() -> None:
                try:
                    profile = self._profile()
                except Exception as exc:  # noqa: BLE001
                    self.window.notify(str(exc), "error")
                    return
                manager = ModManager(profile)
                self.window.run_async(
                    manager.update_all,
                    on_done=lambda changed: self.window.notify(
                        f"Updated {len(changed)} mod(s)"
                        if changed else "Everything already up to date",
                        "success",
                    ),
                )

            update_all.clicked.connect(do_update)
            actions.addWidget(update_all)

        actions.addStretch(1)
        layout.addLayout(actions)
        return page

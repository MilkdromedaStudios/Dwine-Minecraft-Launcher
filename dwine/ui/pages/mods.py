"""Mods & Packs: Modrinth search, one-click installs, updates, presets."""

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
from ...content.presets import PRESETS, install_preset
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
        for profile in self.store.list():
            self.profile_box.addItem(profile.name, profile.slug)
        top.addWidget(self.profile_box, 1)

        self.preset_box = QComboBox()
        for key, preset in PRESETS.items():
            self.preset_box.addItem(f"Preset: {preset.name}", key)
        apply_preset = QPushButton("Install preset")
        apply_preset.clicked.connect(self.apply_preset)
        top.addWidget(self.preset_box)
        top.addWidget(apply_preset)
        layout.addLayout(top)

        tabs = QTabWidget()
        tabs.addTab(self._content_tab("mod"), "Mods")
        tabs.addTab(self._content_tab("resourcepack"), "Resource Packs")
        tabs.addTab(self._content_tab("shader"), "Shaders")
        layout.addWidget(tabs, 1)

    # ------------------------------------------------------------------

    def _profile(self):
        slug = self.profile_box.currentData()
        if not slug:
            raise RuntimeError("Create a profile on the Home tab first.")
        return self.store.load(slug)

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
        button = QPushButton("Search")

        def run_search() -> None:
            query = search.text().strip()
            profile = self._profile()

            def do():
                return modrinth.search(
                    query,
                    project_type=kind,
                    game_version=profile.version or None,
                    loader=profile.loader if kind == "mod" else None,
                )

            def done(hits):
                results.clear()
                for hit in hits:
                    item = QListWidgetItem(
                        f"{hit.title}  ·  {hit.downloads:,} downloads\n"
                        f"    {hit.description[:110]}"
                    )
                    item.setData(Qt.ItemDataRole.UserRole, hit.slug)
                    results.addItem(item)

            self.window.run_async(do, on_done=done)

        button.clicked.connect(run_search)
        search.returnPressed.connect(run_search)
        search_row.addWidget(search, 1)
        search_row.addWidget(button)
        layout.addLayout(search_row)
        layout.addWidget(results, 1)

        actions = QHBoxLayout()
        install = QPushButton("Install selected")
        install.setObjectName("Primary")

        def do_install() -> None:
            item = results.currentItem()
            if not item:
                return
            slug = item.data(Qt.ItemDataRole.UserRole)
            profile = self._profile()
            manager = self._manager(kind, profile)
            self.window.run_async(
                lambda: manager.install(slug),
                on_done=lambda _r: self.window.notify(
                    f"Installed {slug} into {profile.name}", "success"
                ),
            )

        install.clicked.connect(do_install)
        actions.addWidget(install)

        if kind == "mod":
            update_all = QPushButton("Update all")

            def do_update() -> None:
                profile = self._profile()
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

    def apply_preset(self) -> None:
        key = self.preset_box.currentData()
        profile = self._profile()

        def done(report):
            installed, skipped = report["installed"], report["skipped"]
            message = f"Preset installed: {len(installed)} mod(s)"
            if skipped:
                message += f", {len(skipped)} skipped (no build for {profile.version})"
            self.window.notify(message, "success")

        self.window.run_async(lambda: install_preset(profile, key), on_done=done)

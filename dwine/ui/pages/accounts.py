"""Accounts: Microsoft device-code login and account switching."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...launcher import auth
from ...launcher.accounts import AccountStore
from ..widgets import Card


class AccountsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.store = AccountStore()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        card = Card("Microsoft accounts")
        self.code_label = QLabel("")
        self.code_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        self.code_label.setWordWrap(True)

        self.account_list = QListWidget()
        self._reload()

        buttons = QHBoxLayout()
        login = QPushButton("Add Microsoft account")
        login.setObjectName("Primary")
        login.clicked.connect(self._login)
        activate = QPushButton("Set active")
        activate.clicked.connect(self._activate)
        remove = QPushButton("Remove")
        remove.setObjectName("Danger")
        remove.clicked.connect(self._remove)
        buttons.addWidget(login)
        buttons.addWidget(activate)
        buttons.addWidget(remove)
        buttons.addStretch(1)

        card.add(self.account_list)
        card.add_layout(buttons)
        card.add(self.code_label)
        layout.addWidget(card)

        note = QLabel(
            "Dwine uses the official Microsoft device-code flow — the same "
            "one the vanilla launcher uses. Your password never touches Dwine."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch(1)

    def _reload(self) -> None:
        self.account_list.clear()
        active = self.store.active(refresh_if_needed=False)
        for account in self.store.list():
            marker = "●  " if active and account["uuid"] == active["uuid"] else "○  "
            item = QListWidgetItem(marker + account["name"])
            item.setData(Qt.ItemDataRole.UserRole, account["uuid"])
            self.account_list.addItem(item)

    def _login(self) -> None:
        def show_code(url: str, code: str) -> None:
            self.code_label.setText(
                f"Open <b>{url}</b> and enter code <b>{code}</b> to sign in."
            )

        def do_login():
            return auth.start_device_login(show_code)

        def done(session_obj):
            self.store.add(session_obj.as_account())
            self.code_label.setText("")
            self._reload()
            self.window.notify(f"Signed in as {session_obj.name}", "success")

        self.window.run_async(do_login, on_done=done)

    def _selected_uuid(self) -> str | None:
        item = self.account_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _activate(self) -> None:
        uuid = self._selected_uuid()
        if uuid:
            self.store.set_active(uuid)
            self._reload()

    def _remove(self) -> None:
        uuid = self._selected_uuid()
        if uuid:
            self.store.remove(uuid)
            self._reload()

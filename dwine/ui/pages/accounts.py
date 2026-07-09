"""Accounts: Microsoft device-code login and account switching.

Two fixes worth knowing about:

* the device code arrives on a worker thread, so it is forwarded to the
  UI through a queued signal — updating widgets directly from the worker
  silently broke the whole flow;
* Microsoft requires every launcher to bring its own (free) Azure app
  ID, so the page includes the field to paste it — without one, login
  cannot work at all.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core.config import get_config
from ...launcher import auth
from ...launcher.accounts import AccountStore
from ..widgets import Card

AZURE_HELP = (
    "Microsoft requires each launcher to register a free Azure app "
    "(≈5 minutes, once):<br>"
    "1. Open <a href='https://portal.azure.com'>portal.azure.com</a> → "
    "Microsoft Entra ID → App registrations → New registration.<br>"
    "2. Any name · account type <i>Personal Microsoft accounts</i> · no "
    "redirect URI needed.<br>"
    "3. In the app: Authentication → enable <b>Allow public client "
    "flows</b> → Save.<br>"
    "4. Copy the <b>Application (client) ID</b> from Overview and paste "
    "it above."
)


class AccountsPage(QWidget):
    # (verification_url, user_code) — emitted from the login worker thread.
    device_code_ready = Signal(str, str)

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.store = AccountStore()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        # -- one-time setup: the Azure client ID --------------------------
        setup = Card("Login setup (one time)")
        self.client_id_edit = QLineEdit(get_config().get("auth.client_id", ""))
        self.client_id_edit.setPlaceholderText(
            "Azure application (client) ID — required for Microsoft login")
        self.client_id_edit.editingFinished.connect(self._save_client_id)
        setup.add(self.client_id_edit)
        help_label = QLabel(AZURE_HELP)
        help_label.setObjectName("Muted")
        help_label.setWordWrap(True)
        help_label.setOpenExternalLinks(True)
        help_label.setTextFormat(Qt.TextFormat.RichText)
        setup.add(help_label)
        layout.addWidget(setup)

        # -- accounts ------------------------------------------------------
        card = Card("Microsoft accounts")
        self.code_label = QLabel("")
        self.code_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        self.code_label.setWordWrap(True)
        self.code_label.setTextFormat(Qt.TextFormat.RichText)

        self.account_list = QListWidget()
        self._reload()

        buttons = QHBoxLayout()
        self.login_button = QPushButton("Add Microsoft account")
        self.login_button.setObjectName("Primary")
        self.login_button.clicked.connect(self._login)
        activate = QPushButton("Set active")
        activate.clicked.connect(self._activate)
        remove = QPushButton("Remove")
        remove.setObjectName("Danger")
        remove.clicked.connect(self._remove)
        buttons.addWidget(self.login_button)
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

        # Worker thread → UI thread hop for the device code.
        self.device_code_ready.connect(self._show_device_code)

    # ------------------------------------------------------------------

    def _save_client_id(self) -> None:
        value = self.client_id_edit.text().strip()
        get_config().set("auth.client_id", value)
        if value:
            self.window.notify("Client ID saved — you can sign in now.",
                               "success")

    def _reload(self) -> None:
        self.account_list.clear()
        active = self.store.active(refresh_if_needed=False)
        for account in self.store.list():
            marker = "●  " if active and account["uuid"] == active["uuid"] else "○  "
            item = QListWidgetItem(marker + account["name"])
            item.setData(Qt.ItemDataRole.UserRole, account["uuid"])
            self.account_list.addItem(item)

    def _show_device_code(self, url: str, code: str) -> None:
        self.code_label.setText(
            f"Open <a href='{url}'>{url}</a> and enter code "
            f"<b style='font-size:16px'>{code}</b> — waiting for you to "
            "finish signing in …"
        )
        self.code_label.setOpenExternalLinks(True)
        QDesktopServices.openUrl(QUrl(url))

    def _login(self) -> None:
        if not (get_config().get("auth.client_id", "")
                or os.environ.get("DWINE_MSA_CLIENT_ID")):
            self.window.notify(
                "Paste your Azure client ID first (see 'Login setup' above).",
                "warning")
            self.client_id_edit.setFocus()
            return

        def show_code(url: str, code: str) -> None:
            # Runs on the worker thread: hand off through the queued signal.
            self.device_code_ready.emit(url, code)

        def do_login():
            return auth.start_device_login(show_code)

        def done(session_obj):
            self.login_button.setEnabled(True)
            self.store.add(session_obj.as_account())
            self.code_label.setText("")
            self._reload()
            self.window.notify(f"Signed in as {session_obj.name}", "success")

        def failed(message: str) -> None:
            self.login_button.setEnabled(True)
            self.code_label.setText("")
            self.window.notify(f"Login failed: {message}", "error")

        self.login_button.setEnabled(False)
        self.code_label.setText("Requesting a device code from Microsoft …")
        self.window.run_async(do_login, on_done=done, on_error=failed)

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

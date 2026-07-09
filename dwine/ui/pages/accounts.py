"""Accounts: Microsoft link-code login (no setup), offline accounts, switching.

The device code arrives on a worker thread, so it is forwarded to the
UI through a queued signal — updating widgets directly from the worker
silently broke the whole flow.
"""

from __future__ import annotations

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
    "Optional. By default Dwine signs you in with a link code and no "
    "setup at all. If you'd rather run auth through your own (free) "
    "Azure app registration, paste its Application (client) ID here and "
    "Dwine will use it instead: portal.azure.com → Microsoft Entra ID → "
    "App registrations → New registration (account type <i>Personal "
    "Microsoft accounts</i>, no redirect URI), then enable <b>Allow "
    "public client flows</b> under Authentication. New IDs must be "
    "allow-listed by Mojang once via "
    "<a href='https://aka.ms/mce-reviewappid'>aka.ms/mce-reviewappid</a>."
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

        # -- Microsoft login (link code, zero setup) -----------------------
        login_card = Card("Microsoft account")
        login_note = QLabel(
            "Sign in with a <b>link code</b> — click the button, enter the "
            "short code at <b>microsoft.com/link</b> in any browser (even on "
            "your phone), done. No Azure, no app registration, no setup. "
            "Your password never touches Dwine."
        )
        login_note.setObjectName("Muted")
        login_note.setWordWrap(True)
        login_note.setTextFormat(Qt.TextFormat.RichText)
        login_card.add(login_note)

        self.code_label = QLabel("")
        self.code_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        self.code_label.setWordWrap(True)
        self.code_label.setTextFormat(Qt.TextFormat.RichText)

        self.account_list = QListWidget()
        self._reload()

        buttons = QHBoxLayout()
        self.login_button = QPushButton("Sign in with Microsoft")
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

        login_card.add(self.account_list)
        login_card.add_layout(buttons)
        login_card.add(self.code_label)
        layout.addWidget(login_card)

        # -- offline account -----------------------------------------------
        offline = Card("Offline account (singleplayer testing)")
        offline_note = QLabel(
            "A local-only account for testing worlds without signing in. "
            "Offline accounts cannot join online servers and do not prove "
            "game ownership."
        )
        offline_note.setObjectName("Muted")
        offline_note.setWordWrap(True)
        offline.add(offline_note)

        offline_row = QHBoxLayout()
        self.offline_name_edit = QLineEdit("Player")
        self.offline_name_edit.setPlaceholderText("Offline player name")
        add_offline = QPushButton("Add offline account")
        add_offline.clicked.connect(self._add_offline)
        offline_row.addWidget(self.offline_name_edit, 1)
        offline_row.addWidget(add_offline)
        offline.add_layout(offline_row)
        layout.addWidget(offline)

        # -- advanced: custom Azure app ------------------------------------
        advanced = Card("Advanced: your own Azure app (optional)")
        self.client_id_edit = QLineEdit(get_config().get("auth.client_id", ""))
        self.client_id_edit.setPlaceholderText(
            "Azure application (client) ID — leave empty to use the link-code login")
        self.client_id_edit.editingFinished.connect(self._save_client_id)
        advanced.add(self.client_id_edit)
        help_label = QLabel(AZURE_HELP)
        help_label.setObjectName("Muted")
        help_label.setWordWrap(True)
        help_label.setOpenExternalLinks(True)
        help_label.setTextFormat(Qt.TextFormat.RichText)
        advanced.add(help_label)
        layout.addWidget(advanced)
        layout.addStretch(1)

        # Worker thread → UI thread hop for the device code.
        self.device_code_ready.connect(self._show_device_code)

    # ------------------------------------------------------------------

    def _save_client_id(self) -> None:
        value = self.client_id_edit.text().strip()
        get_config().set("auth.client_id", value)
        if value:
            self.window.notify(
                "Custom Azure client ID saved — sign-ins will use it.",
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

    def _add_offline(self) -> None:
        name = self.offline_name_edit.text().strip() or "Player"
        self.store.add(auth.offline_session(name))
        self._reload()
        self.window.notify(
            f"Added offline account {name} for singleplayer testing.",
            "success",
        )

    def _login(self) -> None:
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
        self.code_label.setText("Requesting a link code from Microsoft …")
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

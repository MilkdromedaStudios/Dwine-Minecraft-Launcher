"""Launcher pages, one module each, built lazily by id."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget


def build(page_id: str, window) -> QWidget:
    if page_id == "home":
        from .home import HomePage

        return HomePage(window)
    if page_id == "mods":
        from .mods import ModsPage

        return ModsPage(window)
    if page_id == "logs":
        from .logs import LogsPage

        return LogsPage(window)
    if page_id == "accounts":
        from .accounts import AccountsPage

        return AccountsPage(window)
    if page_id == "settings":
        from .settings import SettingsPage

        return SettingsPage(window)
    return QWidget()

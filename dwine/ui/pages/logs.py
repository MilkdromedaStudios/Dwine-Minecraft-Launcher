"""Logs: live game output plus one-click crash analysis."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core.events import bus
from ...launcher.crash import analyze_file, latest_crash_report
from ...launcher.profiles import ProfileStore


class LogsPage(QWidget):
    log_line = Signal(str)

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.store = ProfileStore()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)

        top = QHBoxLayout()
        top.addWidget(QLabel("Profile:"))
        self.profile_box = QComboBox()
        for profile in self.store.list():
            self.profile_box.addItem(profile.name, profile.slug)
        top.addWidget(self.profile_box, 1)

        analyze = QPushButton("Analyze last crash")
        analyze.setObjectName("Primary")
        analyze.clicked.connect(self._analyze)
        clear = QPushButton("Clear")
        clear.clicked.connect(lambda: self.console.clear())
        top.addWidget(analyze)
        top.addWidget(clear)
        layout.addLayout(top)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(5000)
        mono = QFont("JetBrains Mono, Consolas, Menlo, monospace")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self.console.setFont(mono)
        layout.addWidget(self.console, 1)

        # game.log events arrive from the pump thread → queue via signal
        self.log_line.connect(self.console.appendPlainText)
        bus.on("game.log", lambda _e, p: self.log_line.emit(p.get("line", "")))

    def _analyze(self) -> None:
        slug = self.profile_box.currentData()
        if not slug:
            self.window.notify("No profile selected.", "warning")
            return
        profile = self.store.load(slug)
        report = latest_crash_report(profile.game_dir)
        if report is None:
            self.window.notify("No crash reports found — nice.", "success")
            return
        findings = analyze_file(report)
        self.console.appendPlainText(f"\n=== Crash analysis: {report.name} ===")
        if not findings:
            self.console.appendPlainText(
                "No known pattern matched. The raw report may still help:")
            self.console.appendPlainText(str(report))
        for finding in findings:
            self.console.appendPlainText(f"\n[{finding.title}]")
            self.console.appendPlainText(f"  → {finding.advice}")

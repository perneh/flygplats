"""Modal dialog showing JSON from the API (browse / debug)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QTimer
from PySide6.QtGui import QCloseEvent, QTextCursor
from PySide6.QtWidgets import QDialog, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout


class ApiJsonDialog(QDialog):
    """Read-only view of a JSON-serializable payload."""

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(640, 480)
        layout = QVBoxLayout(self)
        self._text = QPlainTextEdit(self)
        self._text.setReadOnly(True)
        self._text.setObjectName("apiJsonPlainText")
        layout.addWidget(self._text)
        close_btn = QPushButton("Close")
        close_btn.setObjectName("apiJsonCloseButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def set_payload(self, data: Any) -> None:
        self._text.setPlainText(json.dumps(data, indent=2, ensure_ascii=False, default=str))


class LogFileViewerDialog(QDialog):
    """Non-modal log window: stays open while you use the app; appends new lines every second."""

    def __init__(self, path: Path, parent=None) -> None:
        super().__init__(parent)
        self._path = path
        self._last_byte_len = 0
        self.setWindowTitle(f"Log — {path.name} (live)")
        self.setModal(False)
        self.resize(720, 520)
        layout = QVBoxLayout(self)
        hint = QLabel(
            "Window stays open and updates every second. You can keep using the main window."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self._text = QPlainTextEdit(self)
        self._text.setReadOnly(True)
        self._text.setObjectName("logFileViewerPlainText")
        layout.addWidget(self._text)
        close_btn = QPushButton("Close")
        close_btn.setObjectName("logFileViewerCloseButton")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._refresh)
        self._load_initial()
        self._timer.start()

    def _load_initial(self) -> None:
        from golf_desktop.log_setup import flush_log_handlers

        flush_log_handlers()
        if not self._path.exists():
            self._text.setPlainText("(log file not found yet)")
            self._last_byte_len = 0
            return
        data = self._path.read_bytes()
        self._last_byte_len = len(data)
        self._text.setPlainText(data.decode("utf-8", errors="replace"))
        self._scroll_to_end()

    def _refresh(self) -> None:
        from golf_desktop.log_setup import flush_log_handlers

        flush_log_handlers()
        if not self._path.exists():
            return
        try:
            data = self._path.read_bytes()
        except OSError:
            return
        if len(data) < self._last_byte_len:
            self._text.setPlainText(data.decode("utf-8", errors="replace"))
            self._last_byte_len = len(data)
        elif len(data) > self._last_byte_len:
            chunk = data[self._last_byte_len :].decode("utf-8", errors="replace")
            self._text.moveCursor(QTextCursor.MoveOperation.End)
            self._text.insertPlainText(chunk)
            self._last_byte_len = len(data)
        self._scroll_to_end()

    def _scroll_to_end(self) -> None:
        cur = self._text.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        self._text.setTextCursor(cur)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._timer.stop()
        super().closeEvent(event)

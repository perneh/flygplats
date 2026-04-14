"""
End-to-end smoke tests: real ``golf_desktop`` process, X11 window lookup via ``xdotool``, live API.

Requires ``xdotool``, ``DISPLAY``, and network stack for ``127.0.0.1`` (see ``conftest.py`` skip logic).
"""

from __future__ import annotations

import pytest

from support import xdotool_helpers

pytestmark = pytest.mark.xdotool


def test_main_window_registered_under_title(golf_desktop_window_id: str) -> None:
    """The main window title matches ``MainWindow.setWindowTitle`` so automation can find it."""
    assert golf_desktop_window_id.strip()
    int(golf_desktop_window_id)  # xdotool prints a numeric X11 window id


def test_main_window_accepts_focus(golf_desktop_window_id: str) -> None:
    xdotool_helpers.window_activate(golf_desktop_window_id)

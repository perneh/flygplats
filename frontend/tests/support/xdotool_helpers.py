"""Thin wrappers around the ``xdotool`` CLI for X11 GUI smoke tests."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Sequence


def xdotool_available() -> bool:
    return shutil.which("xdotool") is not None


def xdotool_run(args: Sequence[str], *, timeout: float = 60.0) -> str:
    """
    Run ``xdotool`` with the given arguments and return stripped stdout.

    Raises ``FileNotFoundError`` if ``xdotool`` is not installed, or
    ``subprocess.CalledProcessError`` on non-zero exit.
    """
    r = subprocess.run(
        ["xdotool", *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return (r.stdout or "").strip()


def search_window_id_by_name(
    name: str,
    *,
    sync: bool = True,
    only_visible: bool = True,
    timeout: float = 60.0,
) -> str:
    """
    Return the first matching X11 window id (hex string) for windows whose name contains ``name``.

    Uses ``xdotool search --sync`` so the call blocks until a match exists (when ``sync`` is true).
    """
    cmd: list[str] = ["search"]
    if sync:
        cmd.append("--sync")
    if only_visible:
        cmd.append("--onlyvisible")
    cmd.extend(["--name", name])
    out = xdotool_run(cmd, timeout=timeout)
    if not out:
        raise RuntimeError(f"xdotool search returned no window for name {name!r}")
    # Multiple lines possible; prefer the first (usually the main window).
    first = out.splitlines()[0].strip()
    if not first:
        raise RuntimeError(f"xdotool search returned empty first line for name {name!r}")
    return first


def window_activate(window_id: str, *, timeout: float = 30.0) -> None:
    xdotool_run(["windowactivate", window_id], timeout=timeout)

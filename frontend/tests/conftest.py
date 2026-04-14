"""
Frontend test fixtures.

- **pytest-qt / offscreen** (``test_01_canvas.py``): same as today; ``QT_QPA_PLATFORM=offscreen`` in CI.
- **xdotool** (``test_02_xdotool_*.py``): real X11 window, ``xdotool`` CLI, and a **TCP** API
  subprocess — mirrors how the desktop app talks to the backend in production.

**xdotool tests:** CLI ``--xdotool=auto|off|require`` (see repo root ``conftest.py``).
``auto`` skips when ``xdotool``/``DISPLAY`` are missing; ``off`` always skips ``test_02_*``;
``require`` fails collection if those tests are selected but the environment is incomplete.

If ``DISPLAY`` is unset but ``Xvfb`` is installed (e.g. Linux CI/Docker), ``pytest_configure``
starts a virtual framebuffer automatically. Opt out: ``GOLF_NO_AUTO_XVFB=1``. Otherwise use
``xvfb-run -a`` or a real X11 ``DISPLAY`` (e.g. XQuartz on macOS).
"""

from __future__ import annotations

import atexit
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from support import xdotool_helpers

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = REPO_ROOT / "frontend"

_xvfb_process: subprocess.Popen | None = None
_xvfb_start_attempted: bool = False


def _terminate_xvfb() -> None:
    global _xvfb_process
    if _xvfb_process is None:
        return
    if _xvfb_process.poll() is None:
        _xvfb_process.terminate()
        try:
            _xvfb_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _xvfb_process.kill()
    _xvfb_process = None


def _try_start_xvfb_for_headless() -> None:
    """Start Xvfb when DISPLAY is empty so xdotool + Qt see an X server (headless Linux/CI)."""
    global _xvfb_process, _xvfb_start_attempted
    if os.environ.get("DISPLAY", "").strip():
        return
    if os.environ.get("GOLF_NO_AUTO_XVFB", "").strip().lower() in ("1", "true", "yes"):
        return
    if _xvfb_start_attempted:
        return
    _xvfb_start_attempted = True
    xvfb_bin = shutil.which("Xvfb")
    if not xvfb_bin or sys.platform == "win32":
        return
    for display_num in range(99, 120):
        display = f":{display_num}"
        try:
            proc = subprocess.Popen(
                [xvfb_bin, display, "-screen", "0", "1280x1024x24", "-nolisten", "tcp"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            continue
        time.sleep(0.4)
        if proc.poll() is not None:
            continue
        os.environ["DISPLAY"] = display
        _xvfb_process = proc
        atexit.register(_terminate_xvfb)
        return


def pytest_configure(config: pytest.Config) -> None:  # noqa: ARG001
    _try_start_xvfb_for_headless()


def xdotool_environment_ready() -> bool:
    if not xdotool_helpers.xdotool_available():
        return False
    # xdotool targets X11; pure Wayland sessions usually lack a usable DISPLAY for these tests.
    return bool(os.environ.get("DISPLAY", "").strip())


def _xdotool_mode(config: pytest.Config) -> str:
    """``--xdotool`` from repo root ``conftest.py``; default ``auto`` if that plugin was not loaded."""
    return getattr(config.option, "xdotool", "auto")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    mode = _xdotool_mode(config)
    xdotool_items = [i for i in items if i.get_closest_marker("xdotool")]

    if mode == "off":
        skip = pytest.mark.skip(reason="--xdotool=off")
        for item in xdotool_items:
            item.add_marker(skip)
        return

    if mode == "require" and xdotool_items and not xdotool_environment_ready():
        from _pytest.config.exceptions import UsageError

        raise UsageError(
            "xdotool tests are included but the environment is incomplete (xdotool on PATH "
            "and DISPLAY, or install Xvfb for auto-virtual display). "
            "Fix the environment, or use --xdotool=auto to skip those tests, --xdotool=off to skip silently."
        )

    if mode == "auto" and not xdotool_environment_ready():
        skip = pytest.mark.skip(
            reason=(
                "xdotool tests need xdotool on PATH and DISPLAY (install xvfb + auto-Xvfb, "
                "or xvfb-run -a, or set DISPLAY). Use --xdotool=off to skip without this message."
            ),
        )
        for item in xdotool_items:
            item.add_marker(skip)


@pytest.fixture
def live_api_tcp(tmp_path: Path) -> tuple[str, int]:
    """In-process schema + isolated SQLite file + uvicorn on a free port + factory-default."""
    try:
        from support.live_api_server import live_api_server_process
    except ModuleNotFoundError as e:
        pytest.skip(
            f"xdotool live API unavailable ({e}). The slim test-runner image has no SQLAlchemy/backend "
            "app; run `pytest frontend/tests/test_01_canvas.py` here, or install backend deps + "
            "`backend/` on PYTHONPATH for full E2E."
        )
    db = tmp_path / "xdotool_api.db"
    with live_api_server_process(db) as hp:
        yield hp


@pytest.fixture
def golf_desktop_subprocess(live_api_tcp: tuple[str, int]) -> subprocess.Popen:
    """Start ``python -m golf_desktop`` pointed at ``live_api_tcp``; terminate after the test."""
    host, port = live_api_tcp
    env = os.environ.copy()
    env["API_BASE_URL"] = f"http://{host}:{port}"
    env.pop("QT_QPA_PLATFORM", None)
    pp = env.get("PYTHONPATH", "")
    extra = str(FRONTEND_ROOT)
    env["PYTHONPATH"] = extra if not pp else f"{extra}{os.pathsep}{pp}"

    proc = subprocess.Popen(
        [sys.executable, "-m", "golf_desktop"],
        cwd=str(FRONTEND_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.5)
    try:
        if proc.poll() is not None:
            raise RuntimeError(f"golf_desktop exited early with code {proc.returncode}")
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


@pytest.fixture
def golf_desktop_window_id(golf_desktop_subprocess: subprocess.Popen) -> str:
    """Wait until the main window title is registered, then return its X11 window id."""
    _ = golf_desktop_subprocess
    return xdotool_helpers.search_window_id_by_name("Golf Desktop", timeout=90.0)

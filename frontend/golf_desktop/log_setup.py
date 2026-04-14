"""Console logging for the desktop app.

Set ``LOG_LEVEL`` to ``DEBUG``, ``INFO`` (default), ``WARNING``, or ``ERROR``.
HTTP traffic from ``httpx``/``httpcore`` is capped at WARNING so request lines stay readable.

Logs are also written under ``~/.cache/golf_desktop/golf_desktop.log`` (rotating). Use
``get_latest_log_path()`` and ``flush_log_handlers()`` when opening the log in the UI.
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path.home() / ".cache" / "golf_desktop"
LOG_FILE = LOG_DIR / "golf_desktop.log"


def get_latest_log_path() -> Path | None:
    """Newest ``golf_desktop.log*`` in ``LOG_DIR`` by modification time (active + rotated)."""
    if not LOG_DIR.is_dir():
        return None
    paths = sorted(
        LOG_DIR.glob("golf_desktop.log*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return paths[0] if paths else None


def flush_log_handlers() -> None:
    """Flush file handlers so the log viewer sees lines written just before open."""
    for h in logging.getLogger().handlers:
        flush = getattr(h, "flush", None)
        if callable(flush):
            flush()


def configure_logging() -> None:
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    # ``force`` clears prior handlers (e.g. pytest or repeated runs in same process).
    kwargs: dict = {
        "level": level,
        "format": fmt,
        "datefmt": datefmt,
        "stream": sys.stderr,
    }
    if sys.version_info >= (3, 8):
        kwargs["force"] = True
    logging.basicConfig(**kwargs)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_048_576,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

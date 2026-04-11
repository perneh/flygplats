"""Pytest / test-runner: configure root logging from ``LOG_LEVEL`` (stderr, same line format as API)."""

from __future__ import annotations

import logging
import os
import sys

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def configure_pytest_logging() -> None:
    """Idempotent: safe to call from ``conftest`` early."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    fmt = logging.Formatter(_FORMAT, datefmt=_DATE_FMT)

    root = logging.getLogger()
    root.setLevel(level)

    if not root.handlers:
        h = logging.StreamHandler(sys.stderr)
        h.setLevel(level)
        h.setFormatter(fmt)
        root.addHandler(h)
    else:
        root.setLevel(level)

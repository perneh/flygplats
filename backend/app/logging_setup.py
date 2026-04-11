"""Central logging configuration for the API process (stderr, structured line format)."""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config import Settings

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def configure_logging(settings: Settings) -> None:
    """
    Configure the ``app`` logger tree. Uvicorn keeps its own loggers; we attach a handler
    so ``logging.getLogger("app....")`` lines always appear with a consistent format.

    When ``log_file_path`` is set, the same lines are appended to a rotating file (used by ``/dev/log``).
    """
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FMT)

    app_root = logging.getLogger("app")
    app_root.setLevel(level)

    if not app_root.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        app_root.addHandler(handler)

    # Rotating file (same format) for dev log HTTP API
    if settings.log_file_path:
        path = Path(settings.log_file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not any(
            isinstance(h, logging.handlers.RotatingFileHandler) for h in app_root.handlers
        ):
            fh = logging.handlers.RotatingFileHandler(
                path,
                maxBytes=10 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
            fh.setLevel(level)
            fh.setFormatter(formatter)
            app_root.addHandler(fh)

    # With ``log_sql`` + engine ``echo=True``, SQLAlchemy logs under this logger.
    if settings.log_sql:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

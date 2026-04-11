"""Development endpoints: read rotating application log file (see ``app.logging_setup``)."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.services import log_file_reader as log_reader

router = APIRouter()

_MAX_LIMIT = 5000
_MAX_TAIL = 2000


@router.get(
    "/log/meta",
    summary="Log file metadata (path, total lines, last line index)",
)
def get_log_meta() -> dict:
    """
    Return the log file path and line counts. ``last_line`` equals ``line_count`` (1-based index of
    the last line; both are ``0`` if the file is missing or empty).
    """
    path = settings.log_file_path
    n = log_reader.count_lines(path)
    return {
        "log_path": path,
        "line_count": n,
        "last_line": n,
        "exists": bool(path and os.path.isfile(path)),
    }


@router.get(
    "/log",
    summary="Read log lines from a 1-based line number",
)
def get_log_lines(
    from_line: int = Query(1, ge=1, description="First line to return (1-based)"),
    limit: int = Query(100, ge=1, le=_MAX_LIMIT, description="Max lines to return"),
    min_level: str | None = Query(
        None,
        description="Optional minimum level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    ),
) -> dict:
    """Read up to ``limit`` lines starting at ``from_line``. Optionally filter by minimum log level."""
    if min_level:
        try:
            log_reader.normalize_level(min_level)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        sl = log_reader.read_lines_slice(
            settings.log_file_path,
            from_line=from_line,
            limit=limit,
            min_level=min_level,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {
        "log_path": settings.log_file_path,
        "from_line": sl.from_line,
        "limit": sl.limit,
        "min_level": sl.min_level,
        "total_lines": sl.total_lines,
        "lines": sl.lines,
        "returned": len(sl.lines),
    }


@router.get(
    "/log/tail",
    summary="Read the last N lines (optional minimum level)",
)
def get_log_tail(
    lines: int = Query(50, ge=1, le=_MAX_TAIL, description="How many lines from the end"),
    min_level: str | None = Query(
        None,
        description="Optional minimum level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    ),
) -> dict:
    """Return the last ``lines`` log lines (after optional level filter)."""
    if min_level:
        try:
            log_reader.normalize_level(min_level)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        sl = log_reader.read_tail(settings.log_file_path, lines=lines, min_level=min_level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {
        "log_path": settings.log_file_path,
        "from_line": sl.from_line,
        "lines_requested": lines,
        "min_level": sl.min_level,
        "total_lines": sl.total_lines,
        "lines": sl.lines,
        "returned": len(sl.lines),
    }

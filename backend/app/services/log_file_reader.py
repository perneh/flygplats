"""Read line-oriented application log files (format from ``app.logging_setup``)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

_LEVEL_ORDER = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def normalize_level(name: str) -> int:
    u = name.strip().upper()
    if u not in _LEVEL_ORDER:
        raise ValueError(f"Unknown level {name!r}; use one of {list(_LEVEL_ORDER)}")
    return _LEVEL_ORDER[u]


def _parse_level_from_line(line: str) -> int | None:
    parts = line.split("|")
    if len(parts) < 3:
        return None
    raw = parts[1].strip().upper()
    return _LEVEL_ORDER.get(raw)


@dataclass(frozen=True)
class LogSlice:
    """Slice of log lines (``from_line`` is 1-based index of first returned line in file)."""

    from_line: int
    limit: int
    lines: list[str]
    total_lines: int
    min_level: str | None


def count_lines(path: str) -> int:
    if not path or not os.path.isfile(path):
        return 0
    n = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for _ in f:
            n += 1
    return n


def read_lines_slice(
    path: str,
    *,
    from_line: int = 1,
    limit: int = 100,
    min_level: str | None = None,
) -> LogSlice:
    """
    Read up to ``limit`` lines starting at 1-based ``from_line`` in the file.
    If ``min_level`` is set, only lines whose parsed level is >= that threshold are returned
    (still at most ``limit`` lines).
    """
    if from_line < 1:
        raise ValueError("from_line must be >= 1")
    if limit < 1:
        raise ValueError("limit must be >= 1")

    if not path or not os.path.isfile(path):
        return LogSlice(
            from_line=from_line, limit=limit, lines=[], total_lines=0, min_level=min_level
        )

    threshold = normalize_level(min_level) if min_level else None

    with open(path, encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    total_lines = len(all_lines)
    start = from_line - 1
    if start >= total_lines:
        return LogSlice(
            from_line=from_line, limit=limit, lines=[], total_lines=total_lines, min_level=min_level
        )

    segment = all_lines[start:]
    out: list[str] = []

    if threshold is None:
        for line in segment:
            if len(out) >= limit:
                break
            out.append(line.rstrip("\n"))
    else:
        for line in segment:
            if len(out) >= limit:
                break
            lvl = _parse_level_from_line(line)
            if lvl is not None and lvl >= threshold:
                out.append(line.rstrip("\n"))

    first_idx = start + 1
    return LogSlice(
        from_line=first_idx,
        limit=limit,
        lines=out,
        total_lines=total_lines,
        min_level=min_level,
    )


def read_tail(
    path: str,
    *,
    lines: int = 50,
    min_level: str | None = None,
) -> LogSlice:
    """Return the last ``lines`` lines (after optional level filter), newest last in the list."""
    if lines < 1:
        raise ValueError("lines must be >= 1")

    if not path or not os.path.isfile(path):
        return LogSlice(from_line=1, limit=lines, lines=[], total_lines=0, min_level=min_level)

    with open(path, encoding="utf-8", errors="replace") as f:
        all_lines = [ln.rstrip("\n") for ln in f.readlines()]

    total_lines = len(all_lines)
    if total_lines == 0:
        return LogSlice(from_line=1, limit=lines, lines=[], total_lines=0, min_level=min_level)

    if min_level is None:
        chunk = all_lines[-lines:]
        start_line = total_lines - len(chunk) + 1
        return LogSlice(
            from_line=start_line,
            limit=lines,
            lines=chunk,
            total_lines=total_lines,
            min_level=None,
        )

    threshold = normalize_level(min_level)
    matched: list[tuple[int, str]] = []
    for i, line in enumerate(all_lines):
        lvl = _parse_level_from_line(line)
        if lvl is not None and lvl >= threshold:
            matched.append((i + 1, line))

    if not matched:
        return LogSlice(
            from_line=1, limit=lines, lines=[], total_lines=total_lines, min_level=min_level
        )

    last = matched[-lines:]
    return LogSlice(
        from_line=last[0][0],
        limit=lines,
        lines=[t[1] for t in last],
        total_lines=total_lines,
        min_level=min_level,
    )

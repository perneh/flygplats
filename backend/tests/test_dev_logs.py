"""
Tests for GET /api/v1/dev/log*, /dev/log/meta, /dev/log/tail.

Uses a temporary log file (``monkeypatch`` on ``settings.log_file_path``) so tests do not
depend on the host ``/tmp/golf-api.log``.
"""

from __future__ import annotations

import pytest

from app.config import settings

API_PREFIX = "/api/v1"

# Matches ``app.logging_setup`` format: "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
L1 = "2026-04-10 10:00:00 | DEBUG    | app.test | debug-msg"
L2 = "2026-04-10 10:00:01 | INFO     | app.test | info-one"
L3 = "2026-04-10 10:00:02 | INFO     | app.test | info-two"
L4 = "2026-04-10 10:00:03 | ERROR    | app.test | err"


@pytest.fixture
def log_file_path(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Point the API at a temp log file for the duration of the test."""
    path = tmp_path / "test-api.log"
    monkeypatch.setattr(settings, "log_file_path", str(path))
    return path


@pytest.mark.asyncio
async def test_log_meta_when_file_missing(api_client, tmp_path, monkeypatch: pytest.MonkeyPatch):
    missing = tmp_path / "does-not-exist.log"
    monkeypatch.setattr(settings, "log_file_path", str(missing))
    r = await api_client.get(f"{API_PREFIX}/dev/log/meta")
    assert r.status_code == 200
    body = r.json()
    assert body["log_path"] == str(missing)
    assert body["exists"] is False
    assert body["line_count"] == 0
    assert body["last_line"] == 0


@pytest.mark.asyncio
async def test_log_meta_counts_lines(api_client, log_file_path):
    log_file_path.write_text(f"{L1}\n{L2}\n{L3}\n", encoding="utf-8")
    r = await api_client.get(f"{API_PREFIX}/dev/log/meta")
    assert r.status_code == 200
    body = r.json()
    assert body["exists"] is True
    assert body["line_count"] == 3
    assert body["last_line"] == 3


@pytest.mark.asyncio
async def test_log_read_from_line(api_client, log_file_path):
    log_file_path.write_text(f"{L1}\n{L2}\n{L3}\n{L4}\n", encoding="utf-8")
    r = await api_client.get(f"{API_PREFIX}/dev/log", params={"from_line": 2, "limit": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["total_lines"] == 4
    assert body["from_line"] == 2
    assert body["lines"] == [L2, L3]
    assert body["returned"] == 2


@pytest.mark.asyncio
async def test_log_read_with_min_level(api_client, log_file_path):
    log_file_path.write_text(f"{L1}\n{L2}\n{L3}\n", encoding="utf-8")
    r = await api_client.get(
        f"{API_PREFIX}/dev/log",
        params={"from_line": 1, "limit": 10, "min_level": "INFO"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["lines"] == [L2, L3]
    assert body["returned"] == 2


@pytest.mark.asyncio
async def test_log_tail(api_client, log_file_path):
    log_file_path.write_text(f"{L1}\n{L2}\n{L3}\n{L4}\n", encoding="utf-8")
    r = await api_client.get(f"{API_PREFIX}/dev/log/tail", params={"lines": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["lines"] == [L3, L4]
    assert body["returned"] == 2
    assert body["from_line"] == 3


@pytest.mark.asyncio
async def test_log_tail_with_min_level(api_client, log_file_path):
    log_file_path.write_text(f"{L1}\n{L2}\n{L3}\n{L4}\n", encoding="utf-8")
    r = await api_client.get(
        f"{API_PREFIX}/dev/log/tail",
        params={"lines": 5, "min_level": "WARNING"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["lines"] == [L4]
    assert body["returned"] == 1


@pytest.mark.asyncio
async def test_log_invalid_min_level_returns_400(api_client, log_file_path):
    log_file_path.write_text(f"{L1}\n", encoding="utf-8")
    r = await api_client.get(
        f"{API_PREFIX}/dev/log",
        params={"from_line": 1, "limit": 5, "min_level": "NOT_A_LEVEL"},
    )
    assert r.status_code == 400
    r2 = await api_client.get(
        f"{API_PREFIX}/dev/log/tail",
        params={"lines": 5, "min_level": "BAD"},
    )
    assert r2.status_code == 400


@pytest.mark.asyncio
async def test_log_from_line_beyond_file(api_client, log_file_path):
    log_file_path.write_text(f"{L1}\n", encoding="utf-8")
    r = await api_client.get(f"{API_PREFIX}/dev/log", params={"from_line": 10, "limit": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["lines"] == []
    assert body["total_lines"] == 1

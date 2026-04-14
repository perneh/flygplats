"""
Start a real TCP FastAPI process for desktop E2E tests (same routes as production).

Uses an isolated SQLite file and ``Base.metadata.create_all`` (same idea as in-process
``backend/tests/conftest``). After startup, calls ``POST /api/v1/dev/factory-default`` so the
API matches bundled init data.
"""

from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import httpx
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.base import Base

# Register all models on Base.metadata (same pattern as ``backend/alembic/env.py``).
import app.models  # noqa: F401


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _backend_dir() -> Path:
    return _repo_root() / "backend"


def pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _sqlite_async_url(sqlite_path: Path) -> str:
    """SQLAlchemy async SQLite URL for an absolute filesystem path (no sqlalchemy.engine.url import)."""
    return f"sqlite+aiosqlite://{sqlite_path.resolve().as_posix()}"


def create_sqlite_schema(database_url: str) -> None:
    async def _run() -> None:
        engine = create_async_engine(database_url, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_run())


def wait_for_http_ok(url: str, *, attempts: int = 100, delay_s: float = 0.1) -> None:
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            r = httpx.get(url, timeout=2.0)
            if r.status_code == 200:
                return
        except (httpx.RequestError, OSError) as e:
            last_exc = e
        time.sleep(delay_s)
    raise RuntimeError(f"Server at {url} did not become ready: {last_exc!r}")


@contextmanager
def live_api_server_process(sqlite_path: Path) -> Generator[tuple[str, int], None, None]:
    """
    Yield ``(host, port)`` for ``http://host:port`` with a running uvicorn child process.

    Environment: ``DATABASE_URL`` points at ``sqlite_path`` (async driver).
    """
    host = "127.0.0.1"
    port = pick_free_port()
    db_url = _sqlite_async_url(sqlite_path)
    create_sqlite_schema(db_url)

    env = os.environ.copy()
    env["DATABASE_URL"] = db_url

    backend = _backend_dir()
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(backend),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_http_ok(f"http://{host}:{port}/health")
        r = httpx.post(f"http://{host}:{port}/api/v1/dev/factory-default", timeout=60.0)
        if r.status_code != 200:
            raise RuntimeError(f"factory-default failed: {r.status_code} {r.text}")
        yield host, port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

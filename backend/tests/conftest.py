"""
Shared test setup for the API (pytest fixtures).

**In-process (default locally):** ``httpx.AsyncClient`` + ``ASGITransport(app=...)`` mot en
SQLite-databas i RAM — kräver att ``backend/app`` finns på ``PYTHONPATH``.

**HTTP-only (t.ex. test-runner i Docker):** sätt ``PYTEST_API_BASE_URL`` (t.ex.
``http://backend:8000``). Då körs inga app-importer här; testcontainern är bara klient.

Helpers i ``tests/support/api_actions`` tar ``(api_host, api_port, ...)``; klienten binds via
``api_client`` (se ``api_context``).
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from tests.support.test_logging import configure_pytest_logging

configure_pytest_logging()

from tests.support.api_context import bind_api_target, clear_api_target
from tests.support.pytest_api_target import external_api_base_url, host_port_for_api_tests

pytest_plugins = ("tests.support.load_scenario_fixtures",)


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    """
    Skip ``test_05_dev_logs.py`` when using a real HTTP API (env or ``--api-base-url``).

    Those tests monkeypatch ``app.config.settings`` in-process; the slim test-runner image
    has no ``app`` package, and remote API mode cannot patch the server anyway.
    """
    if Path(collection_path).name != "test_05_dev_logs.py":
        return None
    if external_api_base_url(config) is not None:
        return True
    return None


@pytest_asyncio.fixture(autouse=True)
async def _factory_default_when_targeting_remote_api(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[None, None]:
    """
    When tests hit a real backend (``PYTEST_API_BASE_URL``), reset domain data before each test
    so behaviour matches isolated in-memory SQLite runs.
    """
    base = external_api_base_url(request.config)
    if base is None:
        yield
        return

    import httpx

    async with httpx.AsyncClient(base_url=base, timeout=30.0) as client:
        r = await client.post("/api/v1/dev/factory-default")
    assert r.status_code == 200, f"factory-default failed: {r.status_code} {r.text}"
    yield


def pytest_configure(config: pytest.Config) -> None:
    """Optional: set ``PYTEST_LOG_CLI=1`` to mirror logs during test runs (same as ``-o log_cli=true``)."""
    if os.environ.get("PYTEST_LOG_CLI", "").lower() not in ("1", "true", "yes"):
        return
    config.option.log_cli = True  # type: ignore[attr-defined]
    config.option.log_cli_level = os.environ.get("LOG_LEVEL", "INFO")  # type: ignore[attr-defined]
    config.option.log_cli_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"  # type: ignore[attr-defined]
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--api-base-url",
        action="store",
        default=None,
        help=(
            "Run API tests against this base URL (e.g. http://127.0.0.1:8000). "
            "When set, requests use real HTTP; the in-memory test DB is not used."
        ),
    )
    parser.addoption(
        "--api-host",
        action="store",
        default=None,
        help=(
            "With --api-port, base URL is http://HOST:PORT. "
            "Ignored when --api-base-url is set."
        ),
    )
    parser.addoption(
        "--api-port",
        action="store",
        default=None,
        type=int,
        help="Port for --api-host (default 8000 if host is set).",
    )


@pytest.fixture
def api_host(api_client: AsyncClient, request: pytest.FixtureRequest) -> str:
    return host_port_for_api_tests(request.config)[0]


@pytest.fixture
def api_port(api_client: AsyncClient, request: pytest.FixtureRequest) -> int:
    return host_port_for_api_tests(request.config)[1]


@pytest.fixture
def expect_bundled_init_data(request: pytest.FixtureRequest) -> bool:
    """True when pytest targets a real API: each test runs ``factory-default``, which reseeds init JSON."""
    return external_api_base_url(request.config) is not None


@pytest_asyncio.fixture
async def test_db(request: pytest.FixtureRequest) -> AsyncGenerator[async_sessionmaker[Any] | None, None]:
    """
    Fresh in-memory schema per test (in-process mode only).

    When ``PYTEST_API_BASE_URL`` / ``--api-base-url`` targets a real server, yields ``None``.
    """
    if external_api_base_url(request.config) is not None:
        yield None
        return

    # SQLAlchemy and the FastAPI app are only required for in-process tests (slim test-runner image
    # has neither — blackbox mode uses ``--api-base-url`` / ``PYTEST_API_BASE_URL`` only).
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    from app.db.base import Base
    from app.db.session import get_session
    from app.main import app

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _get_session() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session
    yield factory
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def api_client(
    request: pytest.FixtureRequest,
    test_db: async_sessionmaker[Any] | None,  # noqa: ARG001 — ensures DB override runs first in-process
) -> AsyncGenerator[AsyncClient, None]:
    base = external_api_base_url(request.config)
    host, port = host_port_for_api_tests(request.config)

    if base is not None:
        async with AsyncClient(base_url=base, timeout=30.0) as client:
            bind_api_target(client, host, port)
            try:
                yield client
            finally:
                clear_api_target()
        return

    transport = ASGITransport(app=_load_app_for_asgi())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        bind_api_target(client, host, port)
        try:
            yield client
        finally:
            clear_api_target()


def _load_app_for_asgi():
    """Import FastAPI app only for in-process ASGI tests (avoids loading app when using HTTP-only mode)."""
    from app.main import app

    return app

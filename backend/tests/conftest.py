"""
Shared test setup for the API (pytest fixtures).

Testing stack (required for FastAPI in this repo)
  • **httpx.AsyncClient** + **httpx.ASGITransport(app=...)** — calls the ASGI app in-process
    (no TCP port). This matches FastAPI’s recommended approach for async tests.
  • Do **not** use Starlette TestClient here; keep one style: httpx only.

  • Optional **integration mode**: pass ``--api-base-url`` or ``--api-host`` / ``--api-port``
    (or set ``PYTEST_API_BASE_URL``) to run the same tests against a real HTTP server.

Helpers in ``tests/support/api_actions.py`` take ``(api_host, api_port, ...)`` as the first
arguments; the real ``httpx`` client is bound by the ``api_client`` fixture (see ``api_context``).

See: https://fastapi.tiangolo.com/advanced/async-tests/

What is a fixture?
  Pytest injects it by name into test functions (see api_client, test_db below).
"""

import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from tests.support.test_logging import configure_pytest_logging

configure_pytest_logging()

from app.db.base import Base
from app.db.session import get_session
from app.main import app
from tests.support.api_context import bind_api_target, clear_api_target
from tests.support.pytest_api_target import external_api_base_url, host_port_for_api_tests

# Registers fixtures from support modules (e.g. load scenario guards). Fixtures stay inert until a test module uses them.
pytest_plugins = ("tests.support.load_scenario_fixtures",)


def pytest_configure(config: pytest.Config) -> None:
    """Optional: set ``PYTEST_LOG_CLI=1`` to mirror logs during test runs (same as ``-o log_cli=true``)."""
    if os.environ.get("PYTEST_LOG_CLI", "").lower() not in ("1", "true", "yes"):
        return
    # Pytest reads these for the logging plugin
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
    """Host name for the API under test (``test`` in in-process mode). Depends on ``api_client``."""
    return host_port_for_api_tests(request.config)[0]


@pytest.fixture
def api_port(api_client: AsyncClient, request: pytest.FixtureRequest) -> int:
    """Port for the API under test (80 for in-process ``http://test``). Depends on ``api_client``."""
    return host_port_for_api_tests(request.config)[1]


@pytest_asyncio.fixture
async def test_db(request: pytest.FixtureRequest) -> AsyncGenerator[async_sessionmaker[Any] | None, None]:
    """
    Fresh database schema in RAM for each test (in-process mode only).

    In integration mode (remote base URL), yields None and does not touch the app DB.
    """
    base = external_api_base_url(request.config)
    if base is not None:
        yield None
        return

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
    test_db: async_sessionmaker[Any] | None,  # noqa: ARG001 — ensures DB override runs first
) -> AsyncGenerator[AsyncClient, None]:
    """
    Binds an httpx client for the test: in-process ASGI by default, or real HTTP when a base URL is set.

    ``api_actions`` helpers use ``(api_host, api_port, ...)``; those fixtures match the bound client.

    Usage:  async def test_foo(api_client, api_host, api_port):
                await add_player(api_host, api_port, "Ada")
    """
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

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        bind_api_target(client, host, port)
        try:
            yield client
        finally:
            clear_api_target()

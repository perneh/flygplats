"""
Pytest fixtures for the load / integration scenario (``test_load_scenario.py``).

Import via ``pytest_plugins`` in ``conftest.py``; use ``pytestmark`` on the test module
so these do not run for unrelated tests.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

import pytest

from tests.support.pytest_api_target import external_api_base_url


@pytest.fixture(scope="module", autouse=False)
def require_external_api_base_url(request: pytest.FixtureRequest) -> None:
    """
    Require a real HTTP base URL; reject 127.0.0.1/localhost from *inside* Docker (wrong target).

    Set ``PYTEST_ALLOW_DOCKER_LOOPBACK=1`` to skip the Docker loopback check only.
    """
    base = external_api_base_url(request.config)
    if base is None:
        pytest.fail(
            "test_load_scenario must target a real API. Pass --api-base-url, --api-host/--api-port, "
            "or PYTEST_API_BASE_URL. Without that, pytest would use in-process SQLite only."
        )

    if os.environ.get("PYTEST_ALLOW_DOCKER_LOOPBACK") == "1":
        return

    if os.path.exists("/.dockerenv"):
        hostname = urlparse(base).hostname
        if hostname in ("127.0.0.1", "localhost", "::1"):
            pytest.fail(
                "Inside Docker, 127.0.0.1 / localhost is THIS container, not the backend — connection fails. "
                "Use --api-base-url=http://backend:8000 (Compose service on the same network), or "
                "http://host.docker.internal:8000 if the API is published on the host. "
                "See test_load_scenario module docstring. Set PYTEST_ALLOW_DOCKER_LOOPBACK=1 only if you know what you're doing."
            )

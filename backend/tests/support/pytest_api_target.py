"""
Resolve which API host/port the current pytest run targets (in-process vs integration).

Used by ``conftest`` fixtures and documented in ``backend/tests/README.md``.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

import pytest


def external_api_base_url(config: pytest.Config) -> str | None:
    """CLI overrides env; host+port used only when ``--api-base-url`` is absent."""
    opt_url = config.getoption("--api-base-url")
    if opt_url:
        return str(opt_url).rstrip("/")

    env_url = os.environ.get("PYTEST_API_BASE_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")

    host = config.getoption("--api-host")
    if host:
        port = config.getoption("--api-port")
        if port is None:
            port = 8000
        return f"http://{host}:{port}"

    return None


def host_port_from_base_url(base: str) -> tuple[str, int]:
    u = urlparse(base)
    host = u.hostname or "localhost"
    if u.port is not None:
        return host, u.port
    if u.scheme == "https":
        return host, 443
    return host, 80


def host_port_for_api_tests(config: pytest.Config) -> tuple[str, int]:
    """
    Logical (host, port) for the active API target.

    In-process ASGI uses ``http://test`` with default HTTP port — we expose that as
    (``test``, 80) so tests can write ``add_player(api_host, api_port, ...)`` consistently.
    """
    base = external_api_base_url(config)
    if base is not None:
        return host_port_from_base_url(base)
    return "test", 80

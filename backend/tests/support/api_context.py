"""
Bind the active ``httpx.AsyncClient`` for the current test so ``api_actions`` can use
``(api_host, api_port, ...)`` without passing the client through every call.

Set by the ``api_client`` fixture in ``conftest.py``; cleared when the client closes.
"""

from __future__ import annotations

from contextvars import ContextVar

from httpx import AsyncClient

_client: ContextVar[AsyncClient | None] = ContextVar("tests_api_client", default=None)
_expected_host: ContextVar[str | None] = ContextVar("tests_api_expected_host", default=None)
_expected_port: ContextVar[int | None] = ContextVar("tests_api_expected_port", default=None)


def bind_api_target(client: AsyncClient, host: str, port: int) -> None:
    _client.set(client)
    _expected_host.set(host)
    _expected_port.set(port)


def clear_api_target() -> None:
    _client.set(None)
    _expected_host.set(None)
    _expected_port.set(None)


def require_client() -> AsyncClient:
    c = _client.get()
    if c is None:
        raise RuntimeError("No API client bound; ensure the test uses the api_client fixture.")
    return c


def assert_host_port_matches(host: str, port: int) -> None:
    eh = _expected_host.get()
    ep = _expected_port.get()
    if eh is None or ep is None:
        raise RuntimeError("API target host/port not bound.")
    assert (host, port) == (eh, ep), (
        f"Host/port must match the active test target: expected ({eh!r}, {ep}), got ({host!r}, {port})"
    )

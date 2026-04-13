"""
Runs **first** by default (``test_01_`` … ``test_07_`` sort in order). See ``backend/tests/README.md``.

When pytest targets a **real API** (``PYTEST_API_BASE_URL`` or ``--api-base-url``), performs a
single ``POST /api/v1/dev/factory-default`` so shared Postgres starts from a known baseline
before other modules run. Per-test resets still run from ``conftest`` for isolation.

**In-process** runs (SQLite per test): skipped — no shared server state to prime.
"""

import pytest

from tests.support.api_actions import post_factory_default
from tests.support.pytest_api_target import external_api_base_url


@pytest.mark.asyncio
async def test_factory_default_primes_remote_database(request, api_host, api_port, api_client):
    if external_api_base_url(request.config) is None:
        pytest.skip("Only needed when tests hit a real HTTP API (shared database).")
    r = await post_factory_default(api_host, api_port)
    assert r.status_code == 200, r.text
    assert r.json().get("status") == "ok"

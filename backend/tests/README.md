# Backend API tests

## HTTP client for tests: **httpx** (required)

FastAPI tests in this repo use **httpx** only:

- **`httpx.AsyncClient`** with **`httpx.ASGITransport(app=app)`** so requests go straight to the ASGI app (in-process, no real network).
- We do **not** use Starlette’s synchronous `TestClient` for API tests here — one style keeps tests consistent with async FastAPI.

Dependency: `httpx` is listed in `backend/requirements-core.txt`.  
Official guide: [FastAPI — Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/).

## Functional style in `test_api.py`

Tests are written as **small user stories** (what the system should do), not as a dump of HTTP details.

- **`tests/support/api_actions.py`** — naming matches intent. Helpers take **`(api_host, api_port, ...)`** first (reads like calling a real server); the **`api_client`** fixture still creates the actual `httpx` client and binds it for the test. For raw paths use `http_get` / `http_post` / etc. Pure helpers like `filter_rounds_occuring_on_calendar_day` take no HTTP args.
- **Sections** in `test_api.py` — health, players, rounds/shots — mirror product areas.

## Fixtures: `api_host`, `api_port`, and `api_client`

Pytest loads **`conftest.py`** next to the tests. That file defines **fixtures** (shared setup):

| Fixture     | Purpose |
|------------|---------|
| `test_db`  | Creates an **empty in-memory SQLite** database and connects the FastAPI app to it (skipped in integration mode). |
| `api_client` | **Default:** `httpx` via **ASGITransport** (in-process). **Integration mode:** real HTTP to `--api-base-url` or `--api-host` / `--api-port`. Binds the client for `api_actions`. |
| `api_host` / `api_port` | The logical host and port for the target (in-process: `test` and **80**; integration: parsed from the base URL). They **depend on** `api_client` so the client is always active first. |

Typical test — pass **`api_host`** and **`api_port`** into helpers (not `api_client`):

```python
async def test_example(api_host, api_port):
    await add_player(api_host, api_port, "Ada")
```

`test_db` runs first because `api_client` depends on it (see `conftest.py`).

## Reading `test_api.py`

Each `test_*` function is one **scenario**, described in its docstring. Steps are ordinary API calls (`get`, `post`, …) followed by **assertions** (expected status code or JSON fields).

## Run

From the repository root:

```bash
python3 -m pytest backend/tests -v
```

### Same tests against another host (integration)

Point pytest at a **running** API (same routes under `/api/v1/...`). The process uses a normal HTTP client; database state and migrations are whatever that server uses — not the isolated in-memory DB from default runs.

**Options (precedence):**

1. `--api-base-url=http://192.168.1.10:8000` — full base URL (scheme + host + port).
2. `--api-host=192.168.1.10 --api-port=8000` — port defaults to **8000** if you omit `--api-port`.
3. Environment variable `PYTEST_API_BASE_URL` (used when `--api-base-url` is not passed).

Example:

```bash
python3 -m pytest backend/tests -v --api-host=127.0.0.1 --api-port=8000
```

### `test_load_scenario.py` (load / Postgres)

This file **fails** if you run it without `--api-base-url`, `--api-host`, or `PYTEST_API_BASE_URL`, so it cannot pass while only using in-process SQLite. Run it when a real backend is up, or exclude it: `pytest backend/tests --ignore=backend/tests/test_load_scenario.py`.

The `test-runner` Docker image default command **ignores** this file so automated runs stay green without a live API.

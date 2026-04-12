# Backend API tests

Tests live under `backend/tests/` and are run with **pytest** from the **repository root** (see [`pyproject.toml`](../../pyproject.toml) for `testpaths` and default `addopts`).

**Official pytest documentation:** [https://docs.pytest.org/en/stable/](https://docs.pytest.org/en/stable/) — usage, fixtures, plugins, and the [command-line reference](https://docs.pytest.org/en/stable/reference/reference.html#command-line-flags).

---

## Contents

- [Collection order (`test_01` … `test_07`)](#collection-order-test_01--test_07)
- [How tests talk to the API](#how-tests-talk-to-the-api)
- [Fixtures (`conftest.py`)](#fixtures-conftestpy)
- [What to read in this tree](#what-to-read-in-this-tree)
- [Running tests](#running-tests)
- [Useful pytest CLI flags](#useful-pytest-cli-flags)
- [Integration mode (real HTTP)](#integration-mode-real-http)

---

## Collection order (`test_01` … `test_07`)

Pytest collects files in **lexicographic** order by path. Module names use a **two-digit prefix** so suites run in a stable, intentional sequence:

| Order | File | Role |
|------:|------|------|
| 01 | `test_01_remote_session_factory.py` | **Remote API only:** one `POST /dev/factory-default` (skip in-process). |
| 02 | `test_02_init_data_seed.py` | Bundled JSON layout checks (no live DB required). |
| 03 | `test_03_golf_clubs.py` | Golf club catalog API. |
| 04 | `test_04_api.py` | Main user journeys + full `/api/v1` route surface. |
| 05 | `test_05_dev_logs.py` | Dev log endpoints (in-process; not collected when targeting HTTP). |
| 06 | `test_06_match_statistics_suite.py` | Matches + player/course statistics. |
| 07 | `test_07_load_scenario.py` | Heavy load test (**requires** external API); excluded from default Docker `CMD`. |

Adding e.g. `test_02_…` ensures it runs **after** `test_01_…` and **before** `test_03_…` with default collection.

---

## How tests talk to the API

**Default (local / CI):** **`httpx.AsyncClient`** with **`httpx.ASGITransport(app=...)`** so requests hit the FastAPI app **in-process** (no TCP). The **`test_db`** fixture swaps the DB for an **in-memory SQLite** schema per test.

**Docker `test-runner`:** the image does **not** ship `backend/app`; it sets **`PYTEST_API_BASE_URL`** (e.g. `http://backend:8000`) so pytest acts as a **plain HTTP client** against a running backend. See the root [README](../../README.md) and [infra/README.md](../../infra/README.md).

Helpers in **`tests/support/api_actions.py`** take **`(api_host, api_port, ...)`** so calls read like a real server; the **`api_client`** fixture binds the client. Raw paths: `http_get` / `http_post` / `http_patch` / `http_delete`.

FastAPI async testing guide: [FastAPI — Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/).

---

## Fixtures (`conftest.py`)

| Fixture | Role |
|--------|------|
| **`test_db`** | In-memory SQLite + schema for in-process runs; yields `None` when a base URL targets a remote API. |
| **`api_client`** | `httpx` client (ASGI or real HTTP). |
| **`api_host` / `api_port`** | Logical target for helpers (`test` + `80` in-process; parsed from URL in integration mode). |
| **`expect_bundled_init_data`** | `True` when using remote API + factory reseed (see tests that depend on init JSON). |

`pytest_plugins` also loads **`tests/support/load_scenario_fixtures.py`**.

---

## What to read in this tree

See the [collection order](#collection-order-test_01--test_07) table. Support code: `tests/support/` (helpers, `load_scenario_fixtures`, etc.).

---

## Running tests

From the **repository root**:

```bash
python3 -m pytest backend/tests -v
```

Match what CI uses (paths from `pyproject.toml`):

```bash
python3 -m pytest
```

---

## Useful pytest CLI flags

These are standard pytest options; full list: [pytest — How to use pytest / Command-line flags](https://docs.pytest.org/en/stable/how-to/usage.html).

| Goal | Example |
|------|---------|
| **Stop on first failure** | `python3 -m pytest backend/tests -x` |
| **Stop after N failures** | `python3 -m pytest backend/tests --maxfail=3` |
| **Only tests whose names match** | `python3 -m pytest backend/tests -k "api and not load"` |
| **Re-run failures first** | `python3 -m pytest backend/tests --lf` |
| **Extra verbosity** | `python3 -m pytest backend/tests -vv` |
| **Quieter** | `python3 -m pytest backend/tests -q` (overrides `-v` from config) |
| **Traceback style** | `python3 -m pytest --tb=short` (repo default) or `--tb=long` / `--tb=no` |
| **Ignore a file** | `python3 -m pytest backend/tests --ignore=backend/tests/test_07_load_scenario.py` |

**Environment:** `PYTEST_ADDOPTS` is appended (e.g. `export PYTEST_ADDOPTS='-x --tb=long'`).

Default output for this repo is configured in **`pyproject.toml`** (`-v`, `--tb=short`, `-ra`, `--durations=15`, …).

---

## Integration mode (real HTTP)

Point pytest at a **running** API (same routes under `/api/v1/...`). No in-memory app DB in that mode — state is whatever the server uses.

**Precedence:**

1. `pytest --api-base-url=http://127.0.0.1:8000`
2. `pytest --api-host=127.0.0.1 --api-port=8000` (port defaults to 8000)
3. `PYTEST_API_BASE_URL` if CLI flags are absent

Example:

```bash
export PYTEST_API_BASE_URL=http://127.0.0.1:8000
python3 -m pytest backend/tests -v
```

**`test_07_load_scenario.py`** is written to **require** an external base URL; running it without that fails on purpose. Exclude it for a quick local run:

```bash
python3 -m pytest backend/tests --ignore=backend/tests/test_07_load_scenario.py
```

The `test-runner` Docker image default command typically ignores that file as well; see [infra/README.md](../../infra/README.md).

# Tests

- **Backend API tests** — **httpx** + `ASGITransport` for FastAPI: [../backend/tests/README.md](../backend/tests/README.md)

## Run on the host

From the repository root, with dev dependencies installed (`requirements-dev.txt`):

```bash
python3 -m pytest
```

Paths and options are read from the repo **`pyproject.toml`** (`testpaths`, `addopts`).  
`backend/tests/test_load_scenario.py` **requires** `--api-base-url` (or host/port / env); without it that test **errors**. To skip it: `--ignore=backend/tests/test_load_scenario.py`.

### More / less output (pytest flags)

| Goal | Example |
|------|---------|
| Default (repo) | One line per test (`PASSED`/`FAILED`), short tracebacks, **extra summary** for skip/xfail (`-ra`), **slowest 15 tests** (`--durations=15`) — see `[tool.pytest.ini_options]` in `pyproject.toml` |
| Extra verbose | `python3 -m pytest -vv` |
| Quieter | `python3 -m pytest -q` (overrides `-v` from config) |
| Stop on first failure | `python3 -m pytest -x` |
| Only tests matching a name | `python3 -m pytest -k "api and not slow"` |
| Full traceback | `python3 -m pytest --tb=long` |

**Environment:** `PYTEST_ADDOPTS` is appended (e.g. `export PYTEST_ADDOPTS='--durations=30 -vv'`).

GUI tests use **pytest-qt**; for headless runs use `QT_QPA_PLATFORM=offscreen` (set in the `test-runner` Docker image).

## Run inside Docker

The **`test-runner`** image does **not** copy all of `backend/` — only what pytest needs: `backend/app` (the FastAPI app is imported in-process for API tests), `backend/tests`, `backend/init_data`, and `backend/requirements-core.txt`. Alembic, runtime Dockerfiles, etc. stay out of the image.

See [../infra/README.md](../infra/README.md) — section **Test runner service** — for:

- One-shot `pytest` via Compose
- Opening an interactive shell in the `test-runner` image to run `pytest` manually

The image runs **`pytest` without `-q`**, so you get the same **verbose per-test status** as on the host (from `pyproject.toml`). To force quiet in Docker:

```bash
docker compose -f infra/docker-compose.yml --profile tests run --rm -e PYTEST_ADDOPTS=-q test-runner
```

Shared assertions live in `packages/test_support` (`golf_test_support`).

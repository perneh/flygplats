# Tests (monorepo)

Pytest discovers **`backend/tests`** and **`frontend/tests`** (see [`pyproject.toml`](../pyproject.toml)).

**Pytest documentation:** [https://docs.pytest.org/en/stable/](https://docs.pytest.org/en/stable/) · [Command-line usage](https://docs.pytest.org/en/stable/how-to/usage.html)

---

## Documentation in this repo

| README | Topics |
|--------|--------|
| [Root README](../README.md) | Quick start, Docker, desktop app, pre-commit |
| [Backend API tests](../backend/tests/README.md) | httpx fixtures, integration mode, `test_01`–`test_07`, pytest flags (`-x`, …) |
| [Frontend tests](../frontend/tests/README.md) | pytest-qt offscreen canvas; **xdotool** + TCP API + real `golf_desktop` (optional `DISPLAY` / `xvfb-run`) |
| [infra/README.md](../infra/README.md) | Compose, GUI/X11, **test-runner** image |

---

## Run on the host

From the **repository root**, with dev dependencies installed (`requirements-dev.txt`):

```bash
python3 -m pytest
```

Options and search paths come from **`pyproject.toml`** (`testpaths`, `addopts`).

### Stop on first failure

```bash
python3 -m pytest -x
```

Same idea with a limit:

```bash
python3 -m pytest --maxfail=1
```

### More / less output

| Goal | Example |
|------|---------|
| Default (repo) | Short tracebacks, slowest durations — see `[tool.pytest.ini_options]` in `pyproject.toml` |
| Extra verbose | `python3 -m pytest -vv` |
| Quieter | `python3 -m pytest -q` |
| Name filter | `python3 -m pytest -k "api and not load"` |

**`PYTEST_ADDOPTS`** is appended (e.g. `export PYTEST_ADDOPTS='-x --tb=long'`).

### Backend-only

Details and integration mode: **[backend/tests/README.md](../backend/tests/README.md)**.

`backend/tests/test_07_load_scenario.py` **requires** `--api-base-url` (or host/port / env). Without it, that module errors by design. Skip it:

```bash
python3 -m pytest --ignore=backend/tests/test_07_load_scenario.py
```

---

## Run inside Docker (`test-runner`)

The **`test-runner`** image contains **`backend/tests`** and **`backend/init_data`** (JSON fixtures), **not** the full `backend/app` — API tests call **`http://backend:8000`** via **`PYTEST_API_BASE_URL`**.

Start **`db`** and **`backend`** with the same Compose project first, then from the **repository root**:

```bash
docker compose -f infra/docker-compose.yml --profile tests build test-runner
docker compose -f infra/docker-compose.yml --profile tests run --rm -it --entrypoint /bin/bash test-runner
```

Inside the container, **`PYTEST_API_BASE_URL`** defaults to **`http://backend:8000`**. Run **`python -m pytest`**, **`python -m pytest backend/tests`**, etc.

More options (one-shot default `CMD`, load scenario): **[infra/README.md](../infra/README.md)** (Test runner service).

Shared assertions: **`packages/test_support`** (`golf_test_support`). GUI tests use **pytest-qt**; the image sets **`QT_QPA_PLATFORM=offscreen`**.

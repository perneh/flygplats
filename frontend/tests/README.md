# Frontend tests

Tests live under **`frontend/tests`** and run with **pytest** from the **repository root** (see [`pyproject.toml`](../../pyproject.toml) for `testpaths`).

**Pytest documentation:** [https://docs.pytest.org/en/stable/](https://docs.pytest.org/en/stable/)

---

## Layout (same idea as `backend/tests`)

| Order | File | Role |
|------:|------|------|
| 01 | `test_01_canvas.py` | **pytest-qt**, offscreen: `CourseCanvas` + object name smoke. |
| 02 | `test_02_xdotool_main_window.py` | **xdotool**: real desktop process + TCP API + X11 window search. |

Support code: **`support/`** (`live_api_server`, `xdotool_helpers`). Shared fixtures: **`conftest.py`**.

---

## pytest-qt (`test_01`)

Uses **`QT_QPA_PLATFORM=offscreen`** in CI (see root [`tests/README.md`](../../tests/README.md)). No display required.

---

## xdotool (`test_02`)

These tests start:

1. A **uvicorn** subprocess with an isolated **SQLite** file and `POST /api/v1/dev/factory-default`.
2. **`python -m golf_desktop`** with `API_BASE_URL` pointing at that server.
3. **`xdotool search --sync --name 'Golf Desktop'`** to assert the window exists.

**Requirements**

- **`xdotool`** on `PATH`
- A usable **`DISPLAY`** (X11). Options:
  - **Linux headless / Docker:** install **`xvfb`** (and `xdotool`); `conftest.py` starts **`Xvfb`**
    automatically in `pytest_configure` when `DISPLAY` is empty (see `GOLF_NO_AUTO_XVFB` to opt out).
    The **test-runner** image installs both.
  - **Manual:** `xvfb-run -a python -m pytest frontend/tests/test_02_xdotool_main_window.py -v`
  - **macOS:** use a real display (e.g. XQuartz) and set `DISPLAY`, or `brew install xdotool` + `xvfb-run` if available.

Tests are **skipped** when `xdotool` is missing or there is still no `DISPLAY` after auto-`Xvfb` (see `frontend/tests/conftest.py`).

**Run only xdotool tests**

```bash
python -m pytest frontend/tests -m xdotool -v
```

**Control xdotool tests without environment variables** (root `conftest.py`):

| Flag | Effect |
|------|--------|
| `--xdotool=auto` (default) | Skip `test_02_*` if `xdotool`/`DISPLAY` are unavailable. |
| `--xdotool=off` | Always skip xdotool tests (e.g. macOS CI without X11). |
| `--xdotool=require` | Fail collection if xdotool tests are run but the environment is incomplete. |

Example: `python -m pytest frontend/tests --xdotool=off -v`

---

## Run from the repo root

```bash
python -m pytest frontend/tests -v
```

Match the full monorepo suite:

```bash
python -m pytest
```

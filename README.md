# Golf desktop (monorepo)

FastAPI backend, PySide6 desktop client, shared test utilities, and Docker Compose for PostgreSQL, API, GUI, and a dedicated test image.

**Check your machine:** macOS/Linux — `./scripts/setup.sh` · Windows — `powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1` · **Docker Compose (macOS, GUI in Docker):** `./scripts/docker-up.sh up --build` runs a display check first — see [infra/README.md](infra/README.md).

## Quick start (local, no Docker)

1. Create a virtualenv and install dev dependencies **from the repository root**:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

2. Run the API (requires a PostgreSQL URL or use Docker for the database only):

   ```bash
   export DATABASE_URL=postgresql+asyncpg://golf:golf@localhost:5432/golf
   cd backend && alembic upgrade head && cd ..
   uvicorn app.main:app --reload --app-dir backend
   ```

3. Run the desktop app (with the API reachable):

   ```bash
   export API_BASE_URL=http://127.0.0.1:8000
   PYTHONPATH=frontend python -m golf_desktop
   ```

   Use the same virtualenv as step 1 (`requirements-dev.txt` installs backend, frontend, and `golf_test_support`).

4. Run tests:

   ```bash
   python -m pytest backend/tests frontend/tests
   ```

More detail: [infra/README.md](infra/README.md) (Docker Compose, GUI on Linux/X11, test container shell).

## Docker Compose (database + backend + GUI)

From the **repository root**:

```bash
cp .env.example .env   # optional: FRONTEND_DISPLAY, see infra/README.md
./scripts/docker-up.sh up --build
```

(`docker-up.sh` on **macOS** runs **`scripts/check-docker-frontend-display.sh`** before starting **frontend** so you avoid Qt **`could not connect to display`** / xcb errors when X11 is not ready. Use `./scripts/docker-up.sh --skip-frontend-display-check up --build` to bypass, or `docker compose … up db backend` for API+DB only.)

- API: `http://localhost:8000` (see `/health` and `/docs`).
- On **macOS**, full troubleshooting: [infra/README.md](infra/README.md) (XQuartz + TCP, **`FRONTEND_DISPLAY`**, **`QT_X11_NO_MITSHM`**). Easiest fallback: `./scripts/docker-up.sh up --build db backend` and run the GUI on the host.
- On **Linux**, use `infra/docker-compose.linux-x11.yml` and set **`DISPLAY` / `FRONTEND_DISPLAY`** to **`:0`** (see [infra/README.md](infra/README.md)).

## Tests in Docker

The `test-runner` service is behind the Compose **profile** `tests`. See [infra/README.md](infra/README.md) for how to run the default test command and how to open an interactive shell inside the test image to run `pytest` yourself.

## Pre-commit

```bash
pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files
```

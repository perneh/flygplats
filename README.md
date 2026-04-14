# Golf desktop (monorepo)

FastAPI backend, PySide6 desktop client, shared test utilities, and **Docker Compose** for running **all stack components** (database, API, GUI container, optional test runner).

## Documentation index

| Document | Contents |
|----------|----------|
| **[README.md](README.md)** (this file) | Docker Compose (all services), temporary host-desktop workaround, tests, pre-commit |
| **[tests/README.md](tests/README.md)** | Running pytest for the repo, `-x` / `--maxfail`, links to pytest docs |
| **[backend/tests/README.md](backend/tests/README.md)** | API test style, `test_01`–`test_07` collection order, integration mode |
| **[infra/README.md](infra/README.md)** | Docker Compose, GUI/X11, test-runner, Linux overrides |
| **[backend/docs/tournaments_and_statistics.md](backend/docs/tournaments_and_statistics.md)** | Tournaments vs rounds/shots; performance API vs leaderboard |

### Tournaments API (gross scoring)

List tournaments with **`GET /api/v1/tournaments`** (newest `play_date` first, then highest `id`). **Filter lists (no id in path):** **`GET /api/v1/tournaments/drafts`** (not started), **`GET /api/v1/tournaments/started`** (in progress), **`GET /api/v1/tournaments/non-draft`** (started or **finished** — for scorecards/results). Create with **`POST /api/v1/tournaments`**, add **`POST /api/v1/tournaments/participants`** with **`tournament_id`**, `player_id`, and `handicap` (max **75** players), then **`POST /api/v1/tournaments/start`** with **`{"tournament_id": <id>}`** to build **flights** (≤4 players, ordered by **ascending handicap**) and **scorecards** with holes **1–18**. Mark complete with **`POST /api/v1/tournaments/stop`** and **`{"tournament_id": <id>}`** → status **`finished`** (stroke updates on **`POST /api/v1/scorecards/hole`** are then rejected). Record strokes while in progress with **`POST /api/v1/scorecards/hole`** and body `{"scorecard_id", "hole_number", "strokes", "player_id"}`. **Leaderboard**: **`POST /api/v1/tournaments/leaderboard`** with **`{"tournament_id": <id>}`**. **Per-shot distances** (from tracked rounds): **`POST /api/v1/tournaments/shot-detail`** with **`tournament_id`** and **`player_id`** — see **[backend/docs/tournaments_and_statistics.md](backend/docs/tournaments_and_statistics.md)** for how this relates to **`GET /players/{id}/performance`**. Read one tournament with **`POST /api/v1/tournaments/detail`**, list cards with **`POST /api/v1/tournaments/scorecards`**, or fetch a card with **`POST /api/v1/scorecards/detail`** — responses include **`out_total`** (holes 1–9), **`in_total`** (10–18), and **`gross_total`**. See **`backend/tests/test_08_tournaments.py`** for a full flow.

**Example (after `alembic upgrade head` and a running API):**

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/tournaments \
  -H 'Content-Type: application/json' \
  -d '{"name":"Club champs","play_date":"2026-08-15","course_id":1}'
# → 201 {"id":1,"name":"Club champs",...,"status":"draft"}

curl -sS -X POST http://127.0.0.1:8000/api/v1/tournaments/participants \
  -H 'Content-Type: application/json' \
  -d '{"tournament_id":1,"player_id":1,"handicap":12.4}'

curl -sS -X POST http://127.0.0.1:8000/api/v1/tournaments/start \
  -H 'Content-Type: application/json' \
  -d '{"tournament_id":1}'
# → flights + scorecards; status "started"

curl -sS -X POST http://127.0.0.1:8000/api/v1/tournaments/stop \
  -H 'Content-Type: application/json' \
  -d '{"tournament_id":1}'
# → status "finished"

curl -sS -X POST http://127.0.0.1:8000/api/v1/tournaments/scorecards \
  -H 'Content-Type: application/json' \
  -d '{"tournament_id":1}'

curl -sS -X POST http://127.0.0.1:8000/api/v1/scorecards/hole \
  -H 'Content-Type: application/json' \
  -d '{"scorecard_id":1,"hole_number":1,"strokes":4,"player_id":1}'
```

---

## Recommended: run everything with Docker Compose

The intended way to run the **database**, **API**, and **desktop GUI** is Compose. Optional **integration tests** use the `tests` profile.

| Service | Role |
|---------|------|
| `db` | PostgreSQL |
| `backend` | FastAPI on [http://127.0.0.1:8000](http://127.0.0.1:8000) (`/docs`, `/health`) |
| `frontend` | PySide6 app in a container (needs X11 / display — see [infra/README.md](infra/README.md)) |
| `test-runner` | Pytest against the live API (`--profile tests`) |

From the **repository root**:

```bash
cp .env.example .env   # optional: FRONTEND_DISPLAY, etc.
./scripts/docker-up.sh up --build
```

On **macOS**, `docker-up.sh` requires **X11 TCP** on port **6000** (XQuartz) before starting **frontend**. Without the helper:

```bash
docker compose -f infra/docker-compose.yml up --build
```

Compose sets **`DISPLAY=host.docker.internal:0`** by default — it does **not** copy your shell’s **`DISPLAY=:0`** (that would break Qt inside the container). Override only with **`FRONTEND_DISPLAY`** in `.env` if needed.

The GUI window shows through **XQuartz** (X11), not as a normal macOS window on the main desktop — switch to the **XQuartz** app in the Dock to see it. See [infra/README.md — No window on the Mac (XQuartz)](infra/README.md#no-window-on-the-mac-xquartz).

**Tests in Docker** (start `db` + `backend` first, same Compose project):

```bash
docker compose -f infra/docker-compose.yml --profile tests run --rm test-runner
```

For an interactive shell in the test image:

```bash
docker compose -f infra/docker-compose.yml --profile tests run --rm -it --entrypoint /bin/bash test-runner
```

More detail: [infra/README.md](infra/README.md) (XQuartz, Linux X11, load scenario, networking).

---

## Temporary workaround: API in Docker, desktop on the host

Use this **only when you cannot run the GUI in Docker** (for example display or X11 issues) or for a quick local iteration without rebuilding the **frontend** image. It is **not** the long-term setup; prefer the Compose stack above.

1. Start the database and API:

   ```bash
   docker compose -f infra/docker-compose.yml up -d --build db backend
   ```

2. On the **host**, install dev dependencies and run the desktop against the published API:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements-dev.txt
   export API_BASE_URL=http://127.0.0.1:8000
   export LOG_LEVEL=INFO
   PYTHONPATH=frontend python3 -m golf_desktop
   ```

   Optional: `LOG_LEVEL=DEBUG` adds more detail (HTTP response codes, canvas updates). The GUI **View → Show log file…** opens a **non-modal** window (you can keep using the app) that **refreshes every second** from the rotating file under `~/.cache/golf_desktop/`. `requirements-dev.txt` includes backend, frontend, and test tooling so you can run pytest and tools from the same venv.

**Pytest on the host** against the Dockerized API:

```bash
export PYTEST_API_BASE_URL=http://127.0.0.1:8000
python -m pytest backend/tests
```

---

## Alternative: everything local (no Docker)

1. **Virtualenv** (from repo root):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```

2. **API** (PostgreSQL must be reachable):

   ```bash
   export DATABASE_URL=postgresql+asyncpg://golf:golf@localhost:5432/golf
   cd backend && alembic upgrade head && cd ..
   uvicorn app.main:app --reload --app-dir backend
   ```

3. **Desktop** (same as recommended):

   ```bash
   export API_BASE_URL=http://127.0.0.1:8000
   export LOG_LEVEL=INFO
   PYTHONPATH=frontend python3 -m golf_desktop
   ```

4. **Tests** (in-process API + SQLite by default; omit `PYTEST_API_BASE_URL`):

   ```bash
   python -m pytest backend/tests frontend/tests
   ```

---

## Machine setup scripts (optional)

- **macOS / Linux:** `./scripts/setup.sh`
- **Windows:** `powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1`

---

## Pre-commit

```bash
pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files
```

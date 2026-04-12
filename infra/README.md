# Infrastructure (Docker Compose)

All paths below assume the **repository root** as the current working directory.

**Compose project name:** `golf-infra` (set in `infra/docker-compose.yml`). Containers and networks are prefixed `golf-infra-…` instead of the old implicit **`infra-…`** (Compose used to derive the name from the `infra/` directory). If you had an existing Postgres volume from the old name, either migrate data or temporarily set `COMPOSE_PROJECT_NAME=infra` in `.env` until you move the data.

### Build fails: `registry-1.docker.io` / `docker/dockerfile` / “no route to host”

Docker must reach **Docker Hub** to pull base images (`python`, `postgres`, …). Errors mentioning **`dial tcp … :443: connect: no route to host`** (often with an **IPv6** address) usually mean the path to `registry-1.docker.io` is blocked or mis-routed—VPN, firewall, corporate network, or broken IPv6 on the LAN.

This repo’s Dockerfiles **do not** use `# syntax=docker/dockerfile:1`, so BuildKit does **not** need an extra upfront pull of the Dockerfile frontend image (one fewer Hub round-trip).

If pulls still fail, try another network, turn the VPN off or on, or in **Docker Desktop** (macOS) check **Settings → Resources → Network** / experimental options; some users fix Hub access by preferring IPv4 or adjusting proxy settings. Confirm with: `docker pull hello-world`.

## Start the stack (database, API, desktop GUI)

1. **Build and start** every service (recommended on **macOS** — runs a display check before `frontend` starts):

   ```bash
   ./scripts/docker-up.sh up --build
   ```

   On **macOS**, `docker-up.sh` **fails** if X11 is not listening on **TCP port 6000** — enable it in XQuartz (see below). We do **not** auto-attach a Unix-socket override; that path is unreliable on Docker Desktop.

   Optional manual attempt (not recommended on Mac): `docker compose -f infra/docker-compose.yml -f infra/docker-compose.mac-x11-socket.yml up --build`

   Equivalent without `docker-up`:

   ```bash
   docker compose -f infra/docker-compose.yml up --build
   ```

   Bypass the check (not recommended if XQuartz/TCP is not ready):

   ```bash
   ./scripts/docker-up.sh --skip-frontend-display-check up --build
   ```

2. **What you get**

   | Service   | Role |
   |-----------|------|
   | `db`      | PostgreSQL 16 (Alpine) |
   | `backend` | FastAPI on port **8000** |
   | `frontend`| PySide6 app (needs a display; see below) |

3. **API**

   - Base URL from the host: `http://localhost:8000`
   - OpenAPI docs: `http://localhost:8000/docs`
   - Health: `http://localhost:8000/health`

4. **Desktop GUI with Docker**

   ### macOS — recommended: **XQuartz** + **TCP `DISPLAY`**

   **What this means**

   - The **frontend** image runs **Linux** with Qt. It expects an **X11** display.
   - macOS draws the desktop with **Quartz**, not X11. **XQuartz** adds an X11 server so Linux GUI apps can show windows on your Mac.
   - **Docker Desktop** runs containers in a VM. Sharing only `/tmp/.X11-unix` from the Mac is often unreliable, so we use **TCP**: the container sets `DISPLAY` to reach your Mac’s X11 server at **`host.docker.internal:0`** (hostname Docker provides for the host, display **`:0`**).

   **Install XQuartz (pick one)**

   - **Homebrew (recommended):**

     ```bash
     brew install --cask xquartz
     ```

   - **Or** install the pkg from [xquartz.org](https://www.xquartz.org/).

   After installing, **log out and log back in** once (installer recommendation), then start **XQuartz** (e.g. Applications → Utilities → XQuartz).

   **One-time XQuartz settings**

   1. Allow TCP to the X server (needed so the container can connect):

      ```bash
      defaults write org.xquartz.X11 nolisten_tcp -boolean false
      ```

      Quit XQuartz completely and open it again.

   2. Allow connections from localhost (XQuartz’s `xhost`, not the Linux `xhost` in default `PATH`):

      On the **Mac**, `xhost` must use the **local** X11 display (`:0`), not `host.docker.internal:0` (that value is only for **inside** Linux containers). If you exported `DISPLAY=host.docker.internal:0` for Docker, **unset it** before `xhost`:

      ```bash
      export DISPLAY=:0
      /opt/X11/bin/xhost +localhost
      ```

      If you see `unable to open display "host.docker.internal:0"`, your shell still has the wrong `DISPLAY` for native macOS — use `export DISPLAY=:0` as above.

      If you see **`unable to open display ":0"`**, the X server is not running on that display yet: **start the XQuartz app first** and wait until it is fully up. Easiest: from XQuartz’s menu use **Applications → Terminal**, then run `echo "$DISPLAY"` and `/opt/X11/bin/xhost +localhost` there (that terminal usually has the correct `DISPLAY`). You can also check for a socket: `ls /tmp/.X11-unix/` (expect `X0` while XQuartz is running).

   **Start the full stack (db + backend + frontend) from the repo root**

   ```bash
   cp .env.example .env   # optional: set FRONTEND_DISPLAY (see [.env.example](../.env.example))
   docker compose -f infra/docker-compose.yml up --build
   ```

   **`DISPLAY` in the container** comes only from **`FRONTEND_DISPLAY`** in `.env` (see [`.env.example`](../.env.example)), defaulting to **`host.docker.internal:0`**. Your **host shell’s `DISPLAY=:0` is not used** — if it were, Qt would look for a Unix socket **inside the container** and fail with **`could not connect to display :0`**.

   It also sets **`QT_X11_NO_MITSHM=1`**, which avoids many failures when X11 goes over **TCP** (container → Mac). The default macOS setup does **not** mount `/tmp/.X11-unix`.

   ### Error: `could not connect to display :0`

   The GUI container should use **`host.docker.internal:0`** (TCP), not **`:0`**. If logs still show **`:0`**, check **`.env`**: remove **`FRONTEND_DISPLAY=:0`** unless you use the Linux socket override on Linux. Recreate the container after editing: `docker compose -f infra/docker-compose.yml up --build --force-recreate frontend`.

   If you merged **`infra/docker-compose.mac-x11-socket.yml`**, stop using it on Docker Desktop unless you know the socket mount works; enable **XQuartz TCP** and use the default compose file instead.

   **`xcb-cursor` / platform plugin `xcb`** messages are usually **secondary**; fix the display first.

   ### Error: `could not connect to display host.docker.internal:0` (fix this first)

   That means **Qt could not open the X11 connection**. Fix **display networking** before chasing `libxcb-cursor` / “could not load platform plugin xcb” — those messages often appear **after** a failed display connect.

   1. **XQuartz is running** (open it from Applications → Utilities).
   2. **TCP enabled** (needed so display `:0` listens on port **6000**):

      ```bash
      defaults write org.xquartz.X11 nolisten_tcp -boolean false
      ```

      Quit XQuartz fully, then start it again.

   3. **Allow clients** on the Mac (use **`DISPLAY=:0`** here — see note above about `host.docker.internal`):

      ```bash
      export DISPLAY=:0
      /opt/X11/bin/xhost +localhost
      ```

      If it still fails: `/opt/X11/bin/xhost +` (temporary, less strict).

   4. **Verify port 6000 is listening**:

      ```bash
      lsof -nP -iTCP:6000 -sTCP:LISTEN
      ```

      If nothing is listed, TCP is still off — repeat step 2.

   5. **If `host.docker.internal` still fails**, set **`FRONTEND_DISPLAY`** to your **Mac’s LAN IP** (often works better with Docker Desktop):

      ```bash
      ipconfig getifaddr en0
      ```

      Put `FRONTEND_DISPLAY=<that-ip>:0` in `.env`, or:

      ```bash
      export FRONTEND_DISPLAY="$(ipconfig getifaddr en0):0"
      docker compose -f infra/docker-compose.yml up --build
      ```

   6. **Test TCP from a throwaway container**:

      ```bash
      docker run --rm --add-host=host.docker.internal:host-gateway alpine:3.20 \
        sh -c "apk add -q netcat-openbsd && nc -zv host.docker.internal 6000"
      ```

   7. **Helper script (macOS):** `bash scripts/verify-x11-docker-mac.sh`

   ### No window on the Mac (XQuartz)

   The **frontend** container runs **Linux Qt** and talks to **XQuartz** on the Mac. The app window is an **X11 window**, not a normal **native macOS** window on the main desktop.

   - **Bring XQuartz to the front:** click **XQuartz** in the Dock (or use **Cmd+Tab**). The Golf Desktop window usually lives there, not mixed with ordinary app windows.
   - Use the **Window** menu in the **XQuartz** menu bar (top of screen when XQuartz is active) to see open X11 windows.
   - If the stack runs but you still see nothing, check **`docker compose … logs frontend`** for Qt errors; confirm **`lsof … 6000`** shows XQuartz listening.
   - For a **native** macOS window without X11, run the app **on the host** (venv + `API_BASE_URL`) — see [temporary workaround](../README.md#temporary-workaround-api-in-docker-desktop-on-the-host).

   ### Frontend in a full virtual machine (VM)

   Yes — you can run the stack (or only the **frontend** container) **inside a Linux (or other) VM** and still use the **laptop screen**, but you must choose **how** the VM shows graphics:

   | Approach | Idea |
   |----------|------|
   | **VM console (VNC / RDP / SPICE)** | Install a desktop in the VM, run Docker Compose there, connect from the laptop with **VNC Viewer**, **Microsoft Remote Desktop**, or your hypervisor’s **full-screen** / **seamless** mode. The whole VM desktop (including X11/Qt windows) appears on the host monitor. |
   | **Docker Desktop on the Mac** | Already uses a small Linux VM under the hood; the GUI path is **XQuartz** on the Mac — see above. |
   | **X11 over the network** | Linux VM runs Qt with `DISPLAY=<laptop-ip>:0` and **XQuartz** on the Mac listens on TCP (same idea as `host.docker.internal:0`, but the client is the VM’s IP). You must allow the VM in **firewall** / **`xhost`**. |

   There is no magic “pipe only our app” to the bare metal screen without **some** display channel (VNC, RDP, X11, or a native app on the host). For the **simplest native window on macOS**, run **backend in Docker** and **PySide on the host** (venv) — see the [temporary workaround](../README.md#temporary-workaround-api-in-docker-desktop-on-the-host).

   ### macOS — host GUI without XQuartz (temporary workaround)

   If you **cannot** use the **frontend** container (see above), run **db + backend** in Compose and the desktop **on the host**. This matches the [temporary workaround](../README.md#temporary-workaround-api-in-docker-desktop-on-the-host) in the root README — prefer the full Compose stack when possible.

   ```bash
   docker compose -f infra/docker-compose.yml up --build db backend
   export API_BASE_URL=http://127.0.0.1:8000
   PYTHONPATH=frontend python -m golf_desktop
   ```

   ### Linux — X11 Unix socket (not TCP to host)

   ```bash
   xhost +local:docker
   export DISPLAY=${DISPLAY:-:0}
   export FRONTEND_DISPLAY=${FRONTEND_DISPLAY:-$DISPLAY}
   docker compose -f infra/docker-compose.yml -f infra/docker-compose.linux-x11.yml up --build
   ```

   The extra file mounts `/tmp/.X11-unix`. Without `FRONTEND_DISPLAY` / `DISPLAY`, Compose would default to `host.docker.internal:0`, which is wrong on Linux — use **`:0`** (or your socket display).

5. **Stop**

   ```bash
   docker compose -f infra/docker-compose.yml down
   ```

### Qt / xcb in the frontend container (troubleshooting)

If you still see **`could not connect to display`**, fix the **display** section above first. The **`libxcb-cursor` / platform plugin “xcb”** messages are often **secondary** (Qt tries to load the plugin after the X connection fails).

If the display **does** connect but you still see **`Could not load the Qt platform plugin "xcb"`**, **rebuild the frontend image without cache** so Debian libraries are included:

```bash
docker compose -f infra/docker-compose.yml build --no-cache frontend
```

To see which shared library fails to load, run once with debug (Compose service `frontend`):

```yaml
environment:
  QT_DEBUG_PLUGINS: "1"
```

Or one-off:

```bash
docker compose -f infra/docker-compose.yml run --rm -e QT_DEBUG_PLUGINS=1 frontend
```

The first message often mentions `libxcb-cursor`, but the real missing `.so` may be another dependency (for example `libxcb-util` / XKB); the `Dockerfile.frontend` installs the usual Debian runtime set including `libxcb-cursor0`, `libxcb-util1`, and `libxkbcommon-x11-0`.

---

## Test runner service (`test-runner`)

The test image is **not** started by default. It is enabled with the Compose profile **`tests`**.

### Run the default test command (one-shot)

This builds (if needed) and runs the image `CMD` (pytest on backend + frontend tests), then exits:

```bash
docker compose -f infra/docker-compose.yml --profile tests run --rm test-runner
```

### Load scenario (`test_07_load_scenario.py`) against the real backend

That module **fails** if you omit `--api-base-url` / `PYTEST_API_BASE_URL` / `--api-host`, so you do not get a green run that only touched in-memory SQLite.

The default **`test-runner` `CMD`** excludes `test_07_load_scenario.py` so `docker compose run test-runner` still runs the rest of `backend/tests` + `frontend/tests` without a live API. Run the load file explicitly when backend is up.

The load test only calls **factory-default** at the **start** (wipe), then creates data; it does **not** clean up after itself. To see that data in Postgres after pytest finishes, you must hit the running API.

1. Rebuild and start backend + db: `docker compose -f infra/docker-compose.yml up -d --build db backend`
2. From the repo root, run pytest with a base URL (Compose DNS name `backend` works from `test-runner`):

```bash
docker compose -f infra/docker-compose.yml --profile tests run --rm test-runner \
  python -m pytest backend/tests/test_07_load_scenario.py -v --api-base-url=http://backend:8000
```

From the **host** (with backend published on port 8000): `--api-base-url=http://127.0.0.1:8000`.

**Inside the `test-runner` container**, do **not** use `127.0.0.1` — that is the container itself. Use `--api-base-url=http://backend:8000` (same Compose network), or `http://host.docker.internal:8000` to reach the API on the host machine (Docker Desktop).

### “Log in” to the test container (interactive shell)

There is no SSH or separate login. You start a shell **in a new container** from the same image:

```bash
docker compose -f infra/docker-compose.yml --profile tests run --rm -it --entrypoint /bin/bash test-runner
```

You will have a prompt with working directory `/app` (see `Dockerfile.test-runner`). Then run tests manually, for example:

```bash
python -m pytest
python -m pytest -vv
python -m pytest -q
```

Default output follows **`pyproject.toml`** (per-test status, short tracebacks, summary of skips, slowest tests). See [tests/README.md](../tests/README.md).

Environment variables such as `QT_QPA_PLATFORM=offscreen` and `PYTHONPATH` are already set in the image for headless Qt tests.

To leave the shell, type `exit` (the `--rm` flag removes the container when the shell ends).

### If you prefer `docker run` (same image)

After a build, list images and run bash by image name/tag:

```bash
docker compose -f infra/docker-compose.yml --profile tests build test-runner
docker images | grep test-runner   # note IMAGE name
docker run --rm -it --entrypoint /bin/bash <image_name_or_id>
```

Compose project names may prefix the image; using `docker compose run` (above) avoids guessing the tag.

---

## Networking between services

Inside Compose, services resolve each other by **service name** (for example `http://backend:8000`). The host uses `localhost` and published ports.

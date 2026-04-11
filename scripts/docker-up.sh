#!/usr/bin/env bash
# Run docker compose from repo root. On macOS, before `up` that starts the frontend
# service, runs scripts/check-docker-frontend-display.sh --emit-env unless skipped.
# If TCP :0 (port 6000) is unavailable but /tmp/.X11-unix exists, adds
# infra/docker-compose.mac-x11-socket.yml automatically.
#
# Usage (from repo root):
#   ./scripts/docker-up.sh up --build
#   ./scripts/docker-up.sh up --build db backend          # no display check (frontend not started)
#   ./scripts/docker-up.sh --skip-frontend-display-check up --build
#
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

SKIP_CHECK=0
ARGS=()
for a in "$@"; do
  if [[ "$a" == "--skip-frontend-display-check" ]]; then
    SKIP_CHECK=1
    continue
  fi
  ARGS+=("$a")
done

COMPOSE=(docker compose -f "$ROOT/infra/docker-compose.yml")

# Only relevant: `docker compose up ...`
if [[ "${ARGS[0]:-}" != "up" ]]; then
  exec "${COMPOSE[@]}" "${ARGS[@]}"
fi

# Collect service names (first non-option tokens after `up`).
services=()
for ((i = 1; i < ${#ARGS[@]}; i++)); do
  a="${ARGS[i]}"
  [[ "$a" == -* ]] && continue
  services+=("$a")
done

# Start frontend if: no service list (default all), or explicit `frontend` in list.
start_frontend=0
if [[ ${#services[@]} -eq 0 ]]; then
  start_frontend=1
elif printf '%s\n' "${services[@]}" | grep -qx frontend; then
  start_frontend=1
fi

if [[ "$(uname -s)" == "Darwin" && "$SKIP_CHECK" -eq 0 && "$start_frontend" -eq 1 ]]; then
  if ! eval "$(bash "$ROOT/scripts/check-docker-frontend-display.sh" --emit-env)"; then
    echo ""
    echo "Bypass:  $0 --skip-frontend-display-check $*"
    echo "Or API+DB only:  docker compose -f infra/docker-compose.yml up --build db backend"
    exit 1
  fi
  if [[ "${GOLF_X11_TRANSPORT:-}" == socket ]]; then
    echo "Using X11 Unix socket (infra/docker-compose.mac-x11-socket.yml). XQuartz must be running."
    echo ""
    COMPOSE+=( -f "$ROOT/infra/docker-compose.mac-x11-socket.yml" )
  fi
fi

exec "${COMPOSE[@]}" "${ARGS[@]}"

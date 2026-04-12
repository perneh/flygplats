#!/usr/bin/env bash
# Check that the host is ready for the *frontend* container (Qt → X11 on macOS).
#
# Usage:
#   bash scripts/check-docker-frontend-display.sh              # human, warnings only
#   bash scripts/check-docker-frontend-display.sh --strict       # human, strict exit
#   bash scripts/check-docker-frontend-display.sh --emit-env     # for docker-up.sh: prints
#       export GOLF_X11_TRANSPORT=tcp|skip  (stdout only, stderr for errors)
#
# See: infra/README.md, .env.example (FRONTEND_DISPLAY).

set -u

tcp_ok() { command -v lsof &>/dev/null && lsof -nP -iTCP:6000 -sTCP:LISTEN 2>/dev/null | grep -q .; }
socket_ok() { [[ -S /tmp/.X11-unix/X0 ]] || ls /tmp/.X11-unix 2>/dev/null | grep -q .; }

STRICT=0
EMIT_ENV=0
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    --emit-env) EMIT_ENV=1 ;;
  esac
done

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
if [[ ! -t 1 ]] || [[ "$EMIT_ENV" -eq 1 ]]; then RED='' GREEN='' YELLOW='' CYAN='' NC=''; fi

ok() { echo -e "${GREEN}OK${NC} $*"; }
warn() { echo -e "${YELLOW}WARN${NC} $*"; }
bad() { echo -e "${RED}FAIL${NC} $*"; }
info() { echo -e "${CYAN}TIP${NC} $*"; }

emit() {
  echo "$1"
}

if [[ "$(uname -s)" != "Darwin" ]]; then
  if [[ "$EMIT_ENV" -eq 1 ]]; then
    emit "export GOLF_X11_TRANSPORT=skip"
    exit 0
  fi
  echo "== Docker frontend display: skipped (not macOS) =="
  exit 0
fi

# Machine-readable path for docker-up.sh (minimal output on stdout)
if [[ "$EMIT_ENV" -eq 1 ]]; then
  if [[ ! -d /Applications/Utilities/XQuartz.app ]]; then
    echo "XQuartz not installed. Install: brew install --cask xquartz" >&2
    exit 1
  fi
  if tcp_ok; then
    exit 0
  fi
  echo "X11 TCP (port 6000) is not listening — the GUI container needs it (FRONTEND_DISPLAY=host.docker.internal:0)." >&2
  echo "Your shell may have DISPLAY=:0; compose no longer forwards that (it would break Qt inside Docker)." >&2
  echo "Enable TCP:  defaults write org.xquartz.X11 nolisten_tcp -boolean false" >&2
  echo "Quit XQuartz fully, reopen. Then:  export DISPLAY=:0  /opt/X11/bin/xhost +localhost" >&2
  echo "Verify:  lsof -nP -iTCP:6000 -sTCP:LISTEN" >&2
  echo "See infra/README.md (macOS + XQuartz)." >&2
  exit 1
fi

echo "== Docker frontend display check (macOS) =="
echo "   (Avoids: could not connect to display / xcb plugin errors when X11 is not ready)"
echo

FAIL=0

if [[ -d /Applications/Utilities/XQuartz.app ]]; then
  ok "XQuartz.app found"
else
  bad "XQuartz not installed (needed for GUI inside Docker on Mac)."
  echo "   Install: brew install --cask xquartz"
  echo "   Or run API+DB only and GUI on the host — see infra/README.md."
  FAIL=1
fi

if [[ -x /opt/X11/bin/xhost ]]; then
  ok "/opt/X11/bin/xhost present"
else
  warn "/opt/X11/bin/xhost missing — open XQuartz once after install"
fi

echo
echo "TCP port 6000 (DISPLAY :0 over TCP — used with host.docker.internal:0):"
if command -v lsof &>/dev/null; then
  if tcp_ok; then
    lsof -nP -iTCP:6000 -sTCP:LISTEN 2>/dev/null
    ok "Something is listening on 6000"
  else
    bad "Nothing listening on TCP 6000."
    echo "   Fix TCP (then quit XQuartz fully and reopen):"
    echo "     defaults write org.xquartz.X11 nolisten_tcp -boolean false"
    echo "     /opt/X11/bin/xhost +localhost"
    FAIL=1
  fi
else
  warn "lsof not found — cannot verify port 6000"
fi

echo
echo "Unix socket /tmp/.X11-unix (alternative when TCP is off):"
if socket_ok; then
  ok "X11 Unix socket present (/tmp/.X11-unix)"
  if [[ "$FAIL" -eq 1 ]]; then
    info "TCP is still required for docker-up / default compose (host.docker.internal:0). Socket-only overrides are unreliable on Docker Desktop."
    FAIL=0
  fi
else
  bad "No /tmp/.X11-unix socket — start the XQuartz application."
  [[ "$FAIL" -eq 0 ]] && FAIL=1
fi

IP=$(ipconfig getifaddr en0 2>/dev/null || true)
if [[ -n "${IP:-}" ]]; then
  echo
  echo "If TCP works but host.docker.internal fails, try in .env:"
  echo "   FRONTEND_DISPLAY=${IP}:0"
fi

echo
if [[ "$FAIL" -eq 1 ]]; then
  if [[ "$STRICT" -eq 1 ]]; then
    echo -e "${RED}Display check failed (strict).${NC} Fix the items above, or run without frontend:"
    echo "   docker compose -f infra/docker-compose.yml up --build db backend"
    exit 1
  fi
  echo -e "${YELLOW}Display check: not ready for frontend-in-Docker (see above).${NC}"
  exit 0
fi

echo -e "${GREEN}Display check OK.${NC}"
exit 0

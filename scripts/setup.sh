#!/usr/bin/env bash
# Host prerequisite check for this repo (macOS + Linux).
# Usage: bash scripts/setup.sh   or   ./scripts/setup.sh

set -u

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [[ ! -t 1 ]]; then
  RED='' GREEN='' YELLOW='' NC=''
fi

ok() { echo -e "${GREEN}OK${NC} $*"; }
warn() { echo -e "${YELLOW}WARN${NC} $*"; }
bad() { echo -e "${RED}MISSING${NC} $*"; }

REQUIRED_FAILED=0

require_cmd() {
  local name="$1"
  if command -v "$name" &>/dev/null; then
    ok "Found: $name ($(command -v "$name"))"
    return 0
  fi
  bad "Required command not found: $name"
  REQUIRED_FAILED=1
  return 1
}

case "$(uname -s)" in
  Darwin) OS="macOS" ;;
  Linux) OS="Linux" ;;
  *) OS="$(uname -s)" ;;
esac

echo "== Host check ($OS) =="
echo

echo "-- Required --"
require_cmd git || true

if command -v python3 &>/dev/null; then
  if python3 - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
  then
    ok "Python $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")') (>= 3.11)"
  else
    bad "python3 found but need >= 3.11 (got: $(python3 -V 2>&1))"
    REQUIRED_FAILED=1
  fi
else
  bad "python3 not found (need >= 3.11)"
  REQUIRED_FAILED=1
fi

require_cmd docker || true

if command -v docker &>/dev/null; then
  if docker compose version &>/dev/null; then
    ok "Docker Compose plugin: $(docker compose version --short 2>/dev/null || docker compose version 2>/dev/null | head -1)"
  elif command -v docker-compose &>/dev/null; then
    warn "Using legacy docker-compose: $(docker-compose --version)"
    ok "docker-compose is present (consider Docker Compose V2: docker compose)"
  else
    bad "Docker is installed but 'docker compose' / docker-compose not found"
    REQUIRED_FAILED=1
  fi

  if docker info &>/dev/null; then
    ok "Docker daemon is reachable"
  else
    warn "Docker is installed but the daemon is not reachable (start Docker Desktop / docker.service)"
  fi
fi

echo
echo "-- Recommended (dev) --"
if command -v pre-commit &>/dev/null; then
  ok "pre-commit: $(pre-commit --version 2>/dev/null | head -1)"
else
  warn "pre-commit not in PATH (optional: pip install from requirements-dev.txt)"
fi

echo
echo "-- Docker GUI (optional) --"
if [[ "$OS" == "macOS" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  if [[ -x "$SCRIPT_DIR/check-docker-frontend-display.sh" ]]; then
    echo "(macOS) Frontend-in-Docker display check:"
    bash "$SCRIPT_DIR/check-docker-frontend-display.sh" || true
    echo ""
  fi
  if command -v brew &>/dev/null; then
    ok "Homebrew: $(brew --version | head -1)"
  else
    warn "Homebrew not found (optional; useful for: brew install --cask xquartz)"
  fi
elif [[ "$OS" == "Linux" ]]; then
  if command -v xhost &>/dev/null; then
    ok "xhost present (use with infra/docker-compose.linux-x11.yml — see infra/README.md)"
  else
    warn "xhost not in PATH (optional for Linux Docker GUI; install x11-xserver-utils or similar)"
  fi
fi

echo
if [[ "$REQUIRED_FAILED" -ne 0 ]]; then
  echo -e "${RED}Some required checks failed.${NC}"
  exit 1
fi

echo -e "${GREEN}All required checks passed.${NC}"
exit 0

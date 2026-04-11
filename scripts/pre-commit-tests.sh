#!/usr/bin/env bash
# Run from repo root; prefer .venv if present (pytest + deps must be installed there).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="python3"
fi
cd "$ROOT"
case "${1:-}" in
  backend)
    exec "$PY" -m pytest backend/tests -q --tb=short
    ;;
  frontend)
    export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
    exec "$PY" -m pytest frontend/tests -q --tb=short
    ;;
  *)
    echo "usage: $0 backend|frontend" >&2
    exit 1
    ;;
esac

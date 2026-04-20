#!/usr/bin/env bash
# Launch the golf desktop frontend (PySide6). Requires /etc/golf-gui/env from setup.sh.
set -euo pipefail
if [[ -f /etc/golf-gui/env ]]; then
  # shellcheck source=/dev/null
  set -a
  source /etc/golf-gui/env
  set +a
fi
: "${FRONTEND_ROOT:?Set FRONTEND_ROOT in /etc/golf-gui/env}"
: "${FRONTEND_VENV:?Set FRONTEND_VENV in /etc/golf-gui/env}"

export DISPLAY="${DISPLAY:-:0}"
export PYTHONPATH="${FRONTEND_ROOT}/frontend${PYTHONPATH:+:$PYTHONPATH}"
# Prefer X11 session (not Wayland) — this VM is X11-only by design.
export GDK_BACKEND="${GDK_BACKEND:-x11}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"

cd "$FRONTEND_ROOT/frontend"
exec "$FRONTEND_VENV/bin/python" -m golf_desktop "$@"

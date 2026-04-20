#!/usr/bin/env bash
# Run after the X server is up (e.g. from systemd). Relaxes X11 ACL for remote clients.
# SECURITY: Prefer restricting by IP/CIDR; GOLF_X11_OPEN=1 enables "xhost +" (lab only).
set -euo pipefail

export DISPLAY="${DISPLAY:-:0}"

# Wait for X (LightDM / Xorg)
for _ in $(seq 1 60); do
  if xdpyinfo -display "$DISPLAY" &>/dev/null; then
    break
  fi
  sleep 2
done

if ! xdpyinfo -display "$DISPLAY" &>/dev/null; then
  echo "start-x11: X not available on $DISPLAY" >&2
  exit 1
fi

if [[ "${GOLF_X11_OPEN:-0}" == "1" ]]; then
  # Lab only — any host that can reach TCP 6000+n may connect.
  xhost + || true
elif [[ -f /etc/golf-gui/x11-host-allow ]]; then
  # One xhost token per line (see `man xhost`), e.g. inet:10.0.0.5 or SI:hostname:IPv4:addr
  while read -r rule; do
    [[ -z "$rule" || "$rule" =~ ^# ]] && continue
    xhost "$rule" || true
  done </etc/golf-gui/x11-host-allow
else
  # Safer default: local connections only (often not enough for Docker on another host).
  xhost +local: || true
  xhost +SI:localuser:debian || true
fi

exit 0

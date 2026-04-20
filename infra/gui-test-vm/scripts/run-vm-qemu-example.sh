#!/usr/bin/env bash
# Example: run the built qcow2 with SSH + X11 forwarded to the host (adjust paths and firmware).
# Replace QCOW2, FIRMWARE, and qemu-system-* for your platform.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
QCOW2="${1:-$ROOT/output/gui-test-vm.qcow2}"
: "${QEMU_BIN:=qemu-system-aarch64}"
: "${MACHINE:=virt}"
: "${CPU:=host}"
: "${RAM_MB:=8192}"
: "${FIRMWARE:=}" # e.g. /opt/homebrew/share/qemu/edk2-aarch64-code.fd
: "${SSH_FWD_PORT:=2222}"
: "${X11_FWD_PORT:=6000}"
: "${QEMU_DISPLAY:=none}" # e.g. none, cocoa (macOS), sdl, gtk

args=(
  -machine "$MACHINE,accel=hvf"
  -cpu "$CPU"
  -m "$RAM_MB"
  -drive "file=$QCOW2,if=virtio,cache=writeback"
  -netdev "user,id=net0,hostfwd=tcp::${SSH_FWD_PORT}-:22,hostfwd=tcp:0.0.0.0:${X11_FWD_PORT}-:6000"
  -device "virtio-net,netdev=net0"
  -display "$QEMU_DISPLAY"
)

# aarch64 "virt" does not support -vga virtio.
if [[ "$QEMU_BIN" == *"aarch64"* ]] || [[ "$MACHINE" == "virt" ]]; then
  args+=(-device ramfb)
else
  args+=(-vga virtio)
fi
if [[ -n "$FIRMWARE" ]]; then
  args+=(-bios "$FIRMWARE")
fi

echo "Starting VM — SSH: ssh -p ${SSH_FWD_PORT} debian@127.0.0.1"
echo "Display backend: ${QEMU_DISPLAY}"
echo "X11 from host (this machine): DISPLAY=127.0.0.1:0  (port ${X11_FWD_PORT} forwarded to guest :0)"
echo "From Docker Desktop (container → host): DISPLAY=host.docker.internal:0"
exec "$QEMU_BIN" "${args[@]}"

#!/usr/bin/env bash
# Linux helper for GUI test VM lifecycle (Packer + QEMU run + SSH).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VARFILE="${VARFILE:-min-byggfil.pkrvars.hcl}"
QCOW="${ROOT}/output/gui-test-vm.qcow2"

info() { printf "%s\n" "$*"; }
warn() { printf "WARN: %s\n" "$*" >&2; }
die() { printf "ERROR: %s\n" "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

usage() {
  cat <<'EOF'
Usage: scripts/packer-linux.sh <command> [args]

Commands:
  prep         Verify required tools via make prep
  init         Create varfile if missing + ensure checksum + keys
  build        Build qcow2 with make all
  all          prep + init + build
  start-qemu   Start built VM using QEMU example wrapper
  ssh          SSH into VM started by start-qemu (port 2222)
  status       Print quick status for keys/varfile/output
  help         Show this help

Environment:
  VARFILE=<file>        Packer var-file (default: min-byggfil.pkrvars.hcl)
  QEMU_BIN=<binary>     Override qemu binary for start-qemu
  FIRMWARE=<path>       Optional firmware path if your platform needs it
EOF
}

ensure_varfile() {
  if [[ -f "$VARFILE" ]]; then
    info "Varfile exists: $VARFILE"
    return 0
  fi
  cp example.pkrvars.hcl "$VARFILE"
  info "Created varfile from template: $VARFILE"
}

ensure_checksum() {
  if grep -q "REPLACE_WITH_LINE_FROM_SHA512SUMS" "$VARFILE"; then
    info "Injecting checksum into $VARFILE"
    make apply-checksum VARFILE="$VARFILE"
  else
    info "Checksum placeholder not found in $VARFILE (skipping apply-checksum)"
  fi
}

ensure_keys() {
  if [[ -f http/builder && -f http/builder.pub ]]; then
    info "Builder SSH key exists (http/builder + .pub)"
  else
    make keys
  fi
}

cmd_prep() {
  make prep
}

cmd_init() {
  ensure_varfile
  ensure_checksum
  ensure_keys
  info "Init complete."
}

cmd_build() {
  [[ -f "$VARFILE" ]] || die "Missing $VARFILE (run: $0 init)"
  make all VARFILE="$VARFILE"
  [[ -f "$QCOW" ]] || die "Build finished but qcow missing: $QCOW"
  info "Build complete: $QCOW"
}

cmd_all() {
  cmd_prep
  cmd_init
  cmd_build
}

cmd_start_qemu() {
  [[ -f "$QCOW" ]] || die "Missing qcow image: $QCOW (run: $0 build)"
  ./scripts/run-vm-qemu-example.sh "$QCOW"
}

cmd_ssh() {
  [[ -f http/builder ]] || die "Missing private key: http/builder (run: $0 init)"
  exec ssh -i http/builder -o StrictHostKeyChecking=accept-new -p 2222 debian@127.0.0.1
}

cmd_status() {
  info "Root: $ROOT"
  info "Varfile: $VARFILE"
  [[ -f "$VARFILE" ]] && info "  - exists" || info "  - missing"
  [[ -f http/builder ]] && info "Builder key: present" || info "Builder key: missing"
  [[ -f "$QCOW" ]] && info "QCOW: present ($QCOW)" || info "QCOW: missing"
  have packer && packer version | sed 's/^/packer: /' || info "packer: missing"
}

main() {
  local cmd="${1:-help}"
  shift || true
  case "$cmd" in
    prep) cmd_prep "$@" ;;
    init) cmd_init "$@" ;;
    build) cmd_build "$@" ;;
    all) cmd_all "$@" ;;
    start-qemu) cmd_start_qemu "$@" ;;
    ssh) cmd_ssh "$@" ;;
    status) cmd_status "$@" ;;
    help|-h|--help) usage ;;
    *) die "Unknown command: $cmd (use: $0 help)" ;;
  esac
}

main "$@"

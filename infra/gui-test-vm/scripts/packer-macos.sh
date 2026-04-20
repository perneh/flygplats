#!/usr/bin/env bash
# macOS helper for GUI test VM lifecycle (Packer + optional QEMU run).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VARFILE="${VARFILE:-min-byggfil.pkrvars.hcl}"
QCOW="${ROOT}/output/gui-test-vm.qcow2"
DEFAULT_FIRMWARE="/opt/homebrew/share/qemu/edk2-aarch64-code.fd"

info() { printf "%s\n" "$*"; }
warn() { printf "WARN: %s\n" "$*" >&2; }
die() { printf "ERROR: %s\n" "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

upsert_hcl_var() {
  local key="$1"
  local value="$2"
  local file="$3"
  local tmp
  tmp="$(mktemp)"
  awk -v k="$key" -v v="$value" '
    BEGIN { done=0 }
    $0 ~ "^[[:space:]]*#?[[:space:]]*" k "[[:space:]]*=" {
      if (!done) {
        print k " = " v
        done=1
      }
      next
    }
    { print }
    END {
      if (!done) {
        print k " = " v
      }
    }
  ' "$file" >"$tmp"
  mv "$tmp" "$file"
}

extract_hcl_string_var() {
  local key="$1"
  local file="$2"
  awk -F= -v k="$key" '
    $0 ~ "^[[:space:]]*" k "[[:space:]]*=" {
      val=$2
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", val)
      gsub(/^"/, "", val)
      gsub(/"$/, "", val)
      print val
      exit
    }
  ' "$file"
}

usage() {
  cat <<'EOF'
Usage: scripts/packer-macos.sh <command> [args]

Commands:
  prep         Verify/install tools via make prep
  init         Create varfile if missing + ensure checksum + keys
  build        Build qcow2 with make all
  all          prep + init + build
  start-qemu   Start built VM with QEMU example wrapper
  start-and-run-frontend  Start VM in background, wait for SSH, run frontend
  ssh          SSH into VM started by start-qemu (port 2222)
  status       Print quick status for keys/varfile/output
  help         Show this help

Environment:
  VARFILE=<file>        Packer var-file (default: min-byggfil.pkrvars.hcl)
  FIRMWARE=<path>       Override firmware path for start-qemu
  QEMU_BIN=<binary>     Override qemu binary for start-qemu
  START_TIMEOUT=<sec>   SSH wait timeout for start-and-run-frontend (default: 180)
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

validate_frontend_git_url() {
  local effective=""
  effective="$(resolve_frontend_git_url)"

  if [[ -z "$effective" ]]; then
    die "frontend_git_url resolved to empty value. Set it in $VARFILE or unset PKR_VAR_frontend_git_url."
  fi
  if [[ "$effective" == "https://github.com/yourorg/flygplats.git" ]]; then
    die "frontend_git_url still points to placeholder in $VARFILE. Set your real repo URL first."
  fi
}

resolve_frontend_git_url() {
  local effective=""
  if [[ "${PKR_VAR_frontend_git_url+x}" == "x" && -n "${PKR_VAR_frontend_git_url}" ]]; then
    effective="${PKR_VAR_frontend_git_url}"
  else
    effective="$(extract_hcl_string_var "frontend_git_url" "$VARFILE" || true)"
  fi
  printf "%s" "$effective"
}

maybe_set_firmware_hint() {
  if [[ "$(uname -m)" != "arm64" ]]; then
    return 0
  fi
  if grep -qE "^[[:space:]]*firmware[[:space:]]*=" "$VARFILE"; then
    return 0
  fi
  if [[ -f "$DEFAULT_FIRMWARE" ]]; then
    info "Adding firmware to $VARFILE (Apple Silicon default)"
    upsert_hcl_var "firmware" "\"$DEFAULT_FIRMWARE\"" "$VARFILE"
  else
    warn "Apple Silicon detected and default firmware was not found at:"
    warn "  $DEFAULT_FIRMWARE"
    warn "Install qemu via Homebrew and set firmware manually in $VARFILE."
  fi
}

ensure_macos_arm_defaults() {
  if [[ "$(uname -m)" != "arm64" ]]; then
    return 0
  fi
  info "Applying Apple Silicon defaults in $VARFILE"
  upsert_hcl_var "qemu_binary" "\"qemu-system-aarch64\"" "$VARFILE"
  upsert_hcl_var "machine_type" "\"virt\"" "$VARFILE"
  upsert_hcl_var "accelerator" "\"hvf\"" "$VARFILE"
  upsert_hcl_var "cloud_image_url" "\"https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-arm64.qcow2\"" "$VARFILE"
}

cmd_prep() {
  make prep
}

cmd_init() {
  ensure_varfile
  ensure_macos_arm_defaults
  ensure_checksum
  ensure_keys
  validate_frontend_git_url
  maybe_set_firmware_hint
  info "Init complete."
}

cmd_build() {
  [[ -f "$VARFILE" ]] || die "Missing $VARFILE (run: $0 init)"
  local resolved_git_url
  resolved_git_url="$(resolve_frontend_git_url)"
  [[ -n "$resolved_git_url" ]] || die "frontend_git_url resolved empty before build."
  info "Using frontend_git_url: $resolved_git_url"
  env -u PKR_VAR_frontend_git_url -u PKR_VAR_FRONTEND_GIT_URL \
    PKR_VAR_frontend_git_url="$resolved_git_url" \
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
  local fw="${FIRMWARE:-}"
  if [[ -z "$fw" && -f "$DEFAULT_FIRMWARE" ]]; then
    fw="$DEFAULT_FIRMWARE"
  fi
  if [[ -n "$fw" ]]; then
    FIRMWARE="$fw" ./scripts/run-vm-qemu-example.sh "$QCOW"
  else
    warn "No firmware path set. On Apple Silicon this usually fails."
    ./scripts/run-vm-qemu-example.sh "$QCOW"
  fi
}

cmd_start_and_run_frontend() {
  [[ -f "$QCOW" ]] || die "Missing qcow image: $QCOW (run: $0 build)"
  [[ -f http/builder ]] || die "Missing private key: http/builder (run: $0 init)"

  local fw="${FIRMWARE:-}"
  if [[ -z "$fw" && -f "$DEFAULT_FIRMWARE" ]]; then
    fw="$DEFAULT_FIRMWARE"
  fi

  local log_file="$ROOT/output/run-qemu.log"
  local timeout="${START_TIMEOUT:-180}"
  local start_cmd="./scripts/run-vm-qemu-example.sh \"$QCOW\""
  if [[ -n "$fw" ]]; then
    start_cmd="FIRMWARE=\"$fw\" ${start_cmd}"
  fi

  info "Starting VM in background (log: $log_file)"
  # Intentionally detach so we can wait for SSH and trigger frontend startup.
  nohup bash -lc "$start_cmd" >"$log_file" 2>&1 &

  info "Waiting for SSH on 127.0.0.1:2222 (timeout ${timeout}s)"
  local elapsed=0
  while ! ssh -i http/builder -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
    -o ConnectTimeout=5 -p 2222 debian@127.0.0.1 'echo ssh-ready' >/dev/null 2>&1; do
    sleep 3
    elapsed=$((elapsed + 3))
    if (( elapsed >= timeout )); then
      die "Timed out waiting for SSH. Check VM log: $log_file"
    fi
  done

  info "SSH is up. Starting frontend in guest."
  ssh -i http/builder -o StrictHostKeyChecking=accept-new -p 2222 debian@127.0.0.1 \
    'nohup /usr/local/bin/run-frontend.sh >/tmp/run-frontend.log 2>&1 & echo "frontend-started"'

  info "Frontend launch command sent."
  info "Open the VM display (UTM or QEMU viewer) to see Golf Desktop."
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
    start-and-run-frontend) cmd_start_and_run_frontend "$@" ;;
    ssh) cmd_ssh "$@" ;;
    status) cmd_status "$@" ;;
    help|-h|--help) usage ;;
    *) die "Unknown command: $cmd (use: $0 help)" ;;
  esac
}

main "$@"

#!/usr/bin/env bash
# Install or verify host tools for Packer + QEMU builds (gui-test-vm).
# macOS: uses Homebrew when brew is available.
# Linux without brew: prints install hints and exits non-zero if anything is missing.

set -euo pipefail

info() { printf '%s\n' "$*"; }
err() { printf '%s\n' "$*" >&2; }

have() { command -v "$1" >/dev/null 2>&1; }

qemu_wanted_binary() {
  case "$(uname -m)" in
    arm64 | aarch64) echo qemu-system-aarch64 ;;
    *) echo qemu-system-x86_64 ;;
  esac
}

install_via_brew() {
  local pkg="$1"
  if ! have brew; then
    return 1
  fi
  info "Installing ${pkg} via Homebrew..."
  brew install "${pkg}"
}

ensure_curl() {
  if have curl; then
    info "curl: OK"
    return 0
  fi
  if install_via_brew curl; then
    have curl || {
      err "curl still not on PATH after brew install."
      return 1
    }
    info "curl: OK"
    return 0
  fi
  err "curl not found. Install curl or Homebrew (https://brew.sh)."
  return 1
}

ensure_ssh_keygen() {
  if have ssh-keygen; then
    info "ssh-keygen: OK"
    return 0
  fi
  err "ssh-keygen not found (unexpected on macOS/Linux)."
  return 1
}

ensure_packer() {
  if have packer; then
    info "packer: OK"
    return 0
  fi
  # Homebrew core dropped the "packer" name; use HashiCorp tap.
  if have brew; then
    info "Installing packer (hashicorp/tap) via Homebrew..."
    brew tap hashicorp/tap
    brew install hashicorp/tap/packer
    have packer || {
      err "packer still not on PATH after brew install."
      return 1
    }
    info "packer: OK"
    return 0
  fi
  err "packer not found. Install: https://developer.hashicorp.com/packer/downloads"
  err "On macOS, install Homebrew first: https://brew.sh then re-run: make prep"
  return 1
}

ensure_qemu() {
  local want
  want="$(qemu_wanted_binary)"
  if have "${want}"; then
    info "${want}: OK"
    return 0
  fi
  if install_via_brew qemu; then
    have "${want}" || {
      err "Expected ${want} on PATH after brew install qemu. Check brew prefix and PATH."
      return 1
    }
    info "${want}: OK"
    return 0
  fi
  err "Missing ${want} (QEMU system emulator)."
  err "Debian/Ubuntu (example): sudo apt-get update && sudo apt-get install -y qemu-system-arm qemu-system-x86 qemu-utils"
  err "Or install Homebrew (Linux/macOS) and re-run: make prep"
  return 1
}

main() {
  ensure_curl
  ensure_ssh_keygen
  ensure_packer
  ensure_qemu
  info "prep: all required CLI tools are available."
}

main "$@"

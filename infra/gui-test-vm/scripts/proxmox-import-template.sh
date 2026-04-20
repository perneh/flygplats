#!/usr/bin/env bash
# Import a built qcow2 image into Proxmox as a VM (optionally mark as template).
#
# Run this on a Proxmox host (or in a shell with qm/pvesm available).
set -euo pipefail

info() { printf "%s\n" "$*"; }
die() { printf "ERROR: %s\n" "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

usage() {
  cat <<'EOF'
Usage:
  scripts/proxmox-import-template.sh
    --image /path/to/gui-test-vm.qcow2
    --vmid 9100
    --name gui-test-vm
    --storage local-lvm
    [--bridge vmbr0]
    [--memory 8192]
    [--cores 4]
    [--ciuser debian]
    [--ssh-pubkey /path/to/builder.pub]
    [--template]

Description:
  Creates a Proxmox VM, imports qcow2 as disk, attaches cloud-init drive,
  and sets a bootable SCSI disk with VirtIO NIC.

Notes:
  - Must run with privileges that can execute qm/pvesm.
  - If --template is set, the VM is converted to a template at the end.
EOF
}

IMAGE=""
VMID=""
NAME="gui-test-vm"
STORAGE=""
BRIDGE="vmbr0"
MEMORY="8192"
CORES="4"
CIUSER="debian"
SSH_PUBKEY=""
MAKE_TEMPLATE="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image) IMAGE="${2:-}"; shift 2 ;;
    --vmid) VMID="${2:-}"; shift 2 ;;
    --name) NAME="${2:-}"; shift 2 ;;
    --storage) STORAGE="${2:-}"; shift 2 ;;
    --bridge) BRIDGE="${2:-}"; shift 2 ;;
    --memory) MEMORY="${2:-}"; shift 2 ;;
    --cores) CORES="${2:-}"; shift 2 ;;
    --ciuser) CIUSER="${2:-}"; shift 2 ;;
    --ssh-pubkey) SSH_PUBKEY="${2:-}"; shift 2 ;;
    --template) MAKE_TEMPLATE="1"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown argument: $1 (use --help)" ;;
  esac
done

[[ -n "$IMAGE" ]] || die "--image is required"
[[ -n "$VMID" ]] || die "--vmid is required"
[[ -n "$STORAGE" ]] || die "--storage is required"
[[ -f "$IMAGE" ]] || die "Image not found: $IMAGE"

have qm || die "qm command not found (run on Proxmox host)"
have pvesm || die "pvesm command not found (run on Proxmox host)"

if qm status "$VMID" >/dev/null 2>&1; then
  die "VMID $VMID already exists. Pick another VMID."
fi

if ! pvesm status | awk '{print $1}' | rg -x "$STORAGE" >/dev/null; then
  die "Storage '$STORAGE' not found in 'pvesm status'."
fi

SSH_KEY_TMP=""
cleanup() {
  if [[ -n "$SSH_KEY_TMP" && -f "$SSH_KEY_TMP" ]]; then
    rm -f "$SSH_KEY_TMP"
  fi
}
trap cleanup EXIT

info "Creating VM $VMID ($NAME)"
qm create "$VMID" \
  --name "$NAME" \
  --memory "$MEMORY" \
  --cores "$CORES" \
  --net0 "virtio,bridge=${BRIDGE}" \
  --ostype l26 \
  --scsihw virtio-scsi-pci \
  --agent enabled=1 \
  --serial0 socket \
  --vga serial0

info "Importing disk image to storage '$STORAGE' (this can take time)"
qm importdisk "$VMID" "$IMAGE" "$STORAGE" --format qcow2

# Works for common storages that expose imported disks as "<storage>:vm-<vmid>-disk-0"
IMPORTED_DISK="${STORAGE}:vm-${VMID}-disk-0"
info "Attaching imported disk: $IMPORTED_DISK"
qm set "$VMID" --scsi0 "$IMPORTED_DISK"
qm set "$VMID" --boot order=scsi0

info "Adding cloud-init drive and defaults"
qm set "$VMID" --ide2 "${STORAGE}:cloudinit"
qm set "$VMID" --ipconfig0 ip=dhcp
qm set "$VMID" --ciuser "$CIUSER"

if [[ -n "$SSH_PUBKEY" ]]; then
  [[ -f "$SSH_PUBKEY" ]] || die "SSH pubkey file not found: $SSH_PUBKEY"
  SSH_KEY_TMP="$(mktemp)"
  cp "$SSH_PUBKEY" "$SSH_KEY_TMP"
  qm set "$VMID" --sshkeys "$SSH_KEY_TMP"
  info "Configured cloud-init SSH key from: $SSH_PUBKEY"
fi

if [[ "$MAKE_TEMPLATE" == "1" ]]; then
  info "Converting VM $VMID to template"
  qm template "$VMID"
fi

info "Done."
info "VMID: $VMID"
info "Name: $NAME"
if [[ "$MAKE_TEMPLATE" == "1" ]]; then
  info "Type: template"
else
  info "Type: regular VM (start with: qm start $VMID)"
fi

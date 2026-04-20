# GUI test VM on Proxmox (Packer + import)

This guide covers the Proxmox-specific flow for the GUI test VM:

1. Build the image with Packer (`.qcow2` output).
2. Copy the image to a Proxmox host.
3. Import it as a VM or template with cloud-init defaults.
4. Clone/start and run the frontend in the guest.

> Scope: this document replaces Proxmox-specific details from `README.md` so the main guide stays focused on local UTM/QEMU usage.

---

## Prerequisites

### Build machine (macOS or Linux)

- Repository cloned locally
- `packer` and `qemu` available (or use helper scripts below)
- Access to your Proxmox host over SSH/SCP

### Proxmox host

- `qm` and `pvesm` available (standard on Proxmox VE)
- A target storage (for example `local-lvm`)
- A network bridge (for example `vmbr0`)

---

## 1) Build the qcow2 image with Packer

From `infra/gui-test-vm`:

```bash
# macOS helper
./scripts/packer-macos.sh all

# Linux helper
./scripts/packer-linux.sh all
```

The build output is:

`output/gui-test-vm.qcow2`

If you prefer manual Make targets, see `README.md`.

---

## 2) Copy image (and optional SSH pubkey) to Proxmox

From `infra/gui-test-vm` on your build machine:

```bash
scp output/gui-test-vm.qcow2 root@<proxmox-host>:/var/lib/vz/template/qemu/
scp http/builder.pub root@<proxmox-host>:/root/gui-test-vm-builder.pub
```

---

## 3) Import qcow2 into Proxmox as VM/template

On the Proxmox host, run:

```bash
./scripts/proxmox-import-template.sh \
  --image /var/lib/vz/template/qemu/gui-test-vm.qcow2 \
  --vmid 9100 \
  --name gui-test-vm \
  --storage local-lvm \
  --bridge vmbr0 \
  --ssh-pubkey /root/gui-test-vm-builder.pub \
  --template
```

What this does:

- creates VM metadata (`qm create`)
- imports the qcow2 disk (`qm importdisk`)
- attaches imported disk as bootable `scsi0`
- adds cloud-init drive and DHCP defaults
- sets cloud-init user (`debian`)
- optionally injects SSH key
- optionally converts VM to template (`--template`)

### Useful options

- Do not create template yet: omit `--template`
- Different memory/CPU:
  - `--memory 4096`
  - `--cores 2`
- Different bridge/storage:
  - `--bridge vmbr1`
  - `--storage <your-storage>`

---

## 4) Start and access the VM

If imported as a regular VM:

```bash
qm start 9100
```

If imported as a template:

```bash
qm clone 9100 9101 --name gui-test-vm-run-1 --full true
qm start 9101
```

Find the guest IP from Proxmox UI or console, then SSH:

```bash
ssh -i http/builder debian@<guest-ip>
```

If SSH key injection was not used, access via console and configure credentials/cloud-init accordingly.

---

## 5) Start frontend inside the guest

In guest shell:

```bash
/usr/local/bin/run-frontend.sh
```

Then use `xdotool` inside the VM if needed (see `XDOTOOL-LATHUND.md`).

---

## Troubleshooting

- **`VMID already exists`**
  - Use a different `--vmid`.
- **`Storage not found`**
  - Check `pvesm status` and use a valid storage name.
- **Import succeeded but boot fails**
  - Verify disk is attached as `scsi0` and boot order includes `scsi0`.
- **No SSH access**
  - Confirm `--ssh-pubkey` path was valid at import time.
  - Verify guest IP and network bridge settings.


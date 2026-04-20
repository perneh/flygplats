# GUI test VM — Debian cloud (qcow2) + XFCE + X11 TCP for remote GUI automation.
#
# Before `packer build`: run `./scripts/00-prepare-cloud-init.sh` (injects http/builder.pub into http/user-data).
# Prerequisite: `http/builder.pub` — generate with: ssh-keygen -t ed25519 -f http/builder -N "" && cp http/builder.pub http/builder.pub

packer {
  required_version = ">= 1.9.0"
  required_plugins {
    qemu = {
      version = ">= 1.1.0"
      source  = "github.com/hashicorp/qemu"
    }
  }
}

variable "vm_name" {
  type    = string
  default = "gui-test-vm"
}

variable "cpus" {
  type    = number
  default = 4
}

variable "memory" {
  type    = number
  default = 8192
}

variable "disk_size" {
  type    = string
  default = "32G"
}

variable "display_width" {
  type    = number
  default = 1280
}

variable "display_height" {
  type    = number
  default = 800
}

variable "qemu_binary" {
  type    = string
  default = "qemu-system-aarch64"
}

variable "machine_type" {
  type    = string
  default = "virt"
}

variable "accelerator" {
  type    = string
  default = "hvf"
}

variable "firmware" {
  type        = string
  description = "EDK2 for aarch64, e.g. /opt/homebrew/share/qemu/edk2-aarch64-code.fd (Homebrew QEMU on Apple Silicon)."
  default     = ""
}

variable "cloud_image_url" {
  type    = string
  default = "https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-arm64.qcow2"
}

variable "cloud_image_checksum" {
  type        = string
  description = "sha256:... from Debian cloud SHA256SUMS (required)."
}

variable "ssh_username" {
  type    = string
  default = "debian"
}

variable "frontend_source_type" {
  type    = string
  default = "git"
  validation {
    condition     = contains(["git", "artifact"], var.frontend_source_type)
    error_message = "Must be git or artifact."
  }
}

variable "frontend_git_url" {
  type    = string
  default = "https://github.com/example/flygplats.git"
}

variable "frontend_git_ref" {
  type    = string
  default = "main"
}

variable "frontend_install_dir" {
  type    = string
  default = "/opt/flygplats"
}

variable "qemu_display" {
  type    = string
  default = "none"
}

locals {
  output_dir = "${path.root}/output"
}

source "qemu" "gui" {
  vm_name          = "${var.vm_name}.qcow2"
  output_directory = local.output_dir

  disk_image       = true
  use_backing_file = false
  disk_size        = var.disk_size
  format           = "qcow2"

  iso_url      = var.cloud_image_url
  iso_checksum = var.cloud_image_checksum

  disk_interface = "virtio"
  net_device     = "virtio-net"

  communicator = "ssh"
  ssh_username   = var.ssh_username
  ssh_private_key_file = "${path.root}/http/builder"
  ssh_timeout    = "45m"

  headless    = true
  display     = var.qemu_display
  qemu_binary = var.qemu_binary
  machine_type = var.machine_type
  accelerator  = var.accelerator
  cpus         = var.cpus
  memory       = var.memory

  boot_wait = "150s"

  cd_label = "cidata"
  cd_files = [
    "${path.root}/http/meta-data",
    "${path.root}/http/user-data",
  ]

  shutdown_command = "sudo shutdown -P now"

  # aarch64 + virt: -vga virtio is invalid ("Virtio VGA not available"); use `firmware` for EDK2 on Apple Silicon.
  firmware = var.firmware
}

build {
  name    = "gui-test-vm"
  sources = ["source.qemu.gui"]

  provisioner "file" {
    source      = "${path.root}/scripts/start-x11.sh"
    destination = "/tmp/start-x11.sh"
  }

  provisioner "file" {
    source      = "${path.root}/scripts/run-frontend.sh"
    destination = "/tmp/run-frontend.sh"
  }

  provisioner "file" {
    source      = "${path.root}/setup.sh"
    destination = "/tmp/setup.sh"
  }

  provisioner "shell" {
    environment_vars = [
      "DEBIAN_FRONTEND=noninteractive",
      "FRONTEND_SOURCE_TYPE=${var.frontend_source_type}",
      "FRONTEND_GIT_URL=${var.frontend_git_url}",
      "FRONTEND_GIT_REF=${var.frontend_git_ref}",
      "FRONTEND_INSTALL_DIR=${var.frontend_install_dir}",
      "DISPLAY_WIDTH=${var.display_width}",
      "DISPLAY_HEIGHT=${var.display_height}",
    ]
    inline = [
      "chmod +x /tmp/setup.sh /tmp/start-x11.sh /tmp/run-frontend.sh",
      "sudo bash /tmp/setup.sh",
    ]
  }
}

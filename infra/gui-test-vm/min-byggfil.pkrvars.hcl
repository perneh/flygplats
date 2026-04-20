# Copy to example.pkrvars.hcl and adjust. Use:
#   packer build -var-file=example.pkrvars.hcl .
#
# Get sha256 from:
#   curl -sS https://cloud.debian.org/images/cloud/bookworm/latest/SHA512SUMS | grep debian-12-generic-arm64
# (Packer accepts sha256: or sha512: prefixes.)

cloud_image_checksum = "sha512:58091ebc250a0926d47bac1bf459ffc9637a9111a232273caa905661544e42f000075b7b52ab99a06198d5c1c217c81f304c2f9196bbde14b47e92f0c68db0d5"

# Optional: Apple Silicon QEMU firmware (Homebrew)
firmware = "/opt/homebrew/share/qemu/edk2-aarch64-code.fd"

# Your fork / monorepo
frontend_git_url = "https://github.com/perneh/flygplats.git"
frontend_git_ref = "main"
qemu_binary = "qemu-system-aarch64"
machine_type = "virt"
accelerator = "hvf"
cloud_image_url = "https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-arm64.qcow2"

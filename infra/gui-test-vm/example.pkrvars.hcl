# Copy to example.pkrvars.hcl and adjust. Use:
#   packer build -var-file=example.pkrvars.hcl .
#
# Get sha256 from:
#   curl -sS https://cloud.debian.org/images/cloud/bookworm/latest/SHA512SUMS | grep debian-12-generic-arm64
# (Packer accepts sha256: or sha512: prefixes.)

cloud_image_checksum = "sha512:REPLACE_WITH_LINE_FROM_SHA512SUMS"

# Optional: Apple Silicon QEMU firmware (Homebrew)
# firmware = "/opt/homebrew/share/qemu/edk2-aarch64-code.fd"

# Your fork / monorepo
frontend_git_url = "https://github.com/yourorg/flygplats.git"
frontend_git_ref = "main"

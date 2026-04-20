#!/usr/bin/env bash
# Convenience: regenerate cloud-init user-data, init plugins, then packer build (pass extra args to packer).
set -euo pipefail
cd "$(dirname "$0")"
./scripts/00-prepare-cloud-init.sh
packer init .
exec packer build "$@" .

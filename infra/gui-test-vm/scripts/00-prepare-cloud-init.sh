#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PUB="$ROOT/http/builder.pub"
TPL="$ROOT/http/user-data.template.yaml"
OUT="$ROOT/http/user-data"
VM_CONSOLE_PASSWORD="${VM_CONSOLE_PASSWORD:-debian}"
if [[ ! -f "$PUB" ]]; then
  echo "Missing $PUB — run:"
  echo "  ssh-keygen -t ed25519 -f \"$ROOT/http/builder\" -N \"\""
  exit 1
fi
if [[ ! -f "$ROOT/http/builder" ]]; then
  echo "Missing private key $ROOT/http/builder"
  exit 1
fi
if [[ ! -f "$TPL" ]]; then
  echo "Missing template $TPL"
  exit 1
fi
# Use awk + ENVIRON so SSH pubkey and password are never re-parsed by the shell
# (SHA512-crypt hashes contain "$" which breaks sed "...${HASH}...").
export BUILDER_KEY
BUILDER_KEY="$(tr -d '\n\r' <"$PUB")"
export VM_CONSOLE_PASSWORD

awk '
  {
    gsub(/__BUILDER_PUB__/, ENVIRON["BUILDER_KEY"])
    gsub(/__VM_CONSOLE_PASSWORD__/, ENVIRON["VM_CONSOLE_PASSWORD"])
    print
  }
' "$TPL" >"$OUT"
echo "Wrote $OUT"

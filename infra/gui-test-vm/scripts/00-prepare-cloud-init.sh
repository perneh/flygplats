#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PUB="$ROOT/http/builder.pub"
TPL="$ROOT/http/user-data.template.yaml"
OUT="$ROOT/http/user-data"
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
KEY=$(tr -d '\n\r' <"$PUB")
sed "s|__BUILDER_PUB__|${KEY}|g" "$TPL" >"$OUT"
echo "Wrote $OUT"

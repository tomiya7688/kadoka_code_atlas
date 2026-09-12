#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 was not found in PATH." >&2
  exit 1
fi

if [ "$#" -eq 0 ]; then
  echo "Usage: ./context.sh <profile|doc-index|remote-delta|compact-diff|structure-index|validation-plan|policy-check|context-pack> [options]" >&2
  exit 2
fi

exec python3 tools/context_tool.py "$@"

#!/usr/bin/env bash
# Export key vault → modelrouter/.env (primary + __ALT_N alternates).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_activate

DRY=""
OVERWRITE=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY="--dry-run" ;;
    --overwrite) OVERWRITE="--overwrite" ;;
  esac
done

echo "==> Key vault export → .env"
PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -m modelrouter.key_vault export $DRY $OVERWRITE

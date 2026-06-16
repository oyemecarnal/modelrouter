#!/usr/bin/env bash
# Network key vault scrape — discovery (masked) or --collect (policy-gated ingest).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_activate

COLLECT=""
HOST=""
for arg in "$@"; do
  case "$arg" in
    --collect) COLLECT="--collect" ;;
    --host=*) HOST="--host ${arg#*=}" ;;
    --host) ;;
  esac
done

echo "==> Key vault network scrape"
PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -m modelrouter.key_vault scrape $COLLECT $HOST

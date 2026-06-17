#!/usr/bin/env bash
# Ingest local .env __ALT_N lines → vault → export → push to mini.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_activate

RESTART_MINI=0
for arg in "$@"; do
  case "$arg" in
    --restart-mini) RESTART_MINI=1 ;;
  esac
done

echo "==> Vault bootstrap alts"
echo ""

echo "── Ingest __ALT_N from .env"
PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -m modelrouter.key_vault ingest-alts
echo ""

"$ROOT/scripts/vault-sync-alts.sh" $([[ "$RESTART_MINI" -eq 1 ]] && echo --restart-mini)
echo ""
echo "[vault-bootstrap-alts] Done"

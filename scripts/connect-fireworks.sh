#!/usr/bin/env bash
# Phase 2 connector — Fireworks paste-key → local .env → kc-mini (never prints key).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
REMOTE_HOST="${MODELROUTER_REMOTE_HOST:-kc-mini-lan}"
PUSH="${CONNECT_FIREWORKS_PUSH:-1}"
RESTART="${CONNECT_FIREWORKS_RESTART:-1}"

usage() {
  echo "Usage: connect-fireworks.sh [--no-push] [--no-restart]"
  echo "  Paste Fireworks API key (fw_…), save to .env, push to mini, restart gateway."
  echo "  Or set FIREWORKS_API_KEY in environment (non-interactive)."
}

NO_PUSH=0
NO_RESTART=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-push) NO_PUSH=1; shift ;;
    --no-restart) NO_RESTART=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

save_key() {
  FIREWORKS_API_KEY="$1" PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
import os
from pathlib import Path
from modelrouter.env_store import update_env_file, validate_provider_key
key = os.environ.get('FIREWORKS_API_KEY', '')
err = validate_provider_key('FIREWORKS_API_KEY', key)
if err: raise SystemExit(err)
update_env_file(Path('''$ENV_FILE'''), 'FIREWORKS_API_KEY', key)
print('  ok saved to .env (validated)')
"
}

echo "==> Connect Fireworks (ModelRouter connector)"
echo "    Signup: https://fireworks.ai"
echo ""

if [[ -n "${FIREWORKS_API_KEY:-}" ]]; then
  save_key "$FIREWORKS_API_KEY"
elif [[ -f "$ENV_FILE" ]] && grep -q '^FIREWORKS_API_KEY=.' "$ENV_FILE"; then
  read -rp "FIREWORKS_API_KEY already in .env. Replace? [y/N] " REPLACE
  [[ "$REPLACE" == [yY] ]] && { read -rsp "Paste Fireworks key (fw_...): " KEY; echo ""; save_key "$KEY"; }
else
  read -rsp "Paste Fireworks key (fw_...): " KEY
  echo ""
  save_key "$KEY"
fi

[[ "$NO_PUSH" -eq 0 && "$PUSH" -eq 1 ]] && "$ROOT/scripts/push-env-to-mini.sh" FIREWORKS_API_KEY
[[ "$NO_RESTART" -eq 0 && "$RESTART" -eq 1 ]] && ssh -o ConnectTimeout=5 "$REMOTE_HOST" 'cd ~/dev/modelrouter && make restart' 2>/dev/null || true
echo "==> Done."

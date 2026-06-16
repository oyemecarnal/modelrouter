#!/usr/bin/env bash
# Phase 2 connector — DeepSeek paste-key → local .env → kc-mini (never prints key).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
REMOTE_HOST="${MODELROUTER_REMOTE_HOST:-kc-mini-lan}"
PUSH="${CONNECT_DEEPSEEK_PUSH:-1}"
RESTART="${CONNECT_DEEPSEEK_RESTART:-1}"

usage() {
  echo "Usage: connect-deepseek.sh [--no-push] [--no-restart]"
  echo "  Paste DeepSeek API key (sk-…), save to .env, push to mini, restart gateway."
  echo "  Or set DEEPSEEK_API_KEY in environment (non-interactive)."
  echo "  Docs: docs/ENV.md"
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
  DEEPSEEK_API_KEY="$1" PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
import os
from pathlib import Path
from modelrouter.env_store import update_env_file, validate_provider_key

key = os.environ.get('DEEPSEEK_API_KEY', '')
err = validate_provider_key('DEEPSEEK_API_KEY', key)
if err:
    raise SystemExit(err)
update_env_file(Path('''$ENV_FILE'''), 'DEEPSEEK_API_KEY', key)
print('  ok saved to .env (validated)')
"
}

echo "==> Connect DeepSeek (ModelRouter connector)"
echo "    Signup: https://platform.deepseek.com"
echo "    Routes: cheap / fast fallbacks"
echo "    Docs: docs/ENV.md · docs/CONNECTOR_SPEC.md"
echo ""

if [[ -n "${DEEPSEEK_API_KEY:-}" ]]; then
  KEY="$DEEPSEEK_API_KEY"
  echo "Using DEEPSEEK_API_KEY from environment."
  save_key "$KEY"
elif [[ -f "$ENV_FILE" ]] && grep -q '^DEEPSEEK_API_KEY=.' "$ENV_FILE"; then
  read -rp "DEEPSEEK_API_KEY already in .env. Replace? [y/N] " REPLACE
  if [[ "$REPLACE" == [yY] ]]; then
    read -rsp "Paste DeepSeek API key (sk-...): " KEY
    echo ""
    save_key "$KEY"
  else
    echo "Keeping existing key (will still push/restart if enabled)."
  fi
else
  read -rsp "Paste DeepSeek API key (sk-...): " KEY
  echo ""
  save_key "$KEY"
fi

if [[ "$NO_PUSH" -eq 0 && "$PUSH" -eq 1 ]]; then
  echo ""
  echo "── Push to ${REMOTE_HOST}"
  "$ROOT/scripts/push-env-to-mini.sh" DEEPSEEK_API_KEY
else
  echo "── Skip push (--no-push)"
fi

if [[ "$NO_RESTART" -eq 0 && "$RESTART" -eq 1 ]]; then
  echo ""
  echo "── Restart gateway on ${REMOTE_HOST}"
  if ssh -o ConnectTimeout=5 "$REMOTE_HOST" 'cd ~/dev/modelrouter && make restart' 2>/dev/null; then
    echo "  ok mini gateway restarted"
  else
    echo "  warn mini restart failed — run: ssh ${REMOTE_HOST} 'cd ~/dev/modelrouter && make restart'"
  fi
else
  echo "── Skip restart (--no-restart)"
fi

echo ""
echo "==> Done. Verify: make check-key-hygiene && make doctor"

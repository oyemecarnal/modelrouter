#!/usr/bin/env bash
# Phase 2 connector MVP — Groq paste-key → local .env → kc-mini (never prints key).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
REMOTE_HOST="${MODELROUTER_REMOTE_HOST:-kc-mini-lan}"
PUSH="${CONNECT_GROQ_PUSH:-1}"
RESTART="${CONNECT_GROQ_RESTART:-1}"

usage() {
  echo "Usage: connect-groq.sh [--no-push] [--no-restart]"
  echo "  Paste Groq API key (gsk_…), save to .env, push to mini, restart gateway."
  echo "  Or set GROQ_API_KEY in environment (non-interactive)."
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
  GROQ_API_KEY="$1" PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
import os
from pathlib import Path
from modelrouter.env_store import update_env_file, validate_provider_key

key = os.environ.get('GROQ_API_KEY', '')
err = validate_provider_key('GROQ_API_KEY', key)
if err:
    raise SystemExit(err)
update_env_file(Path('''$ENV_FILE'''), 'GROQ_API_KEY', key)
print('  ok saved to .env (validated)')
"
}

echo "==> Connect Groq (ModelRouter connector MVP)"
echo "    Signup: https://console.groq.com/keys"
echo "    Spec: docs/CONNECTOR_SPEC.md"
echo ""

if [[ -n "${GROQ_API_KEY:-}" ]]; then
  KEY="$GROQ_API_KEY"
  echo "Using GROQ_API_KEY from environment."
  save_key "$KEY"
elif [[ -f "$ENV_FILE" ]] && grep -q '^GROQ_API_KEY=.' "$ENV_FILE"; then
  read -rp "GROQ_API_KEY already in .env. Replace? [y/N] " REPLACE
  if [[ "$REPLACE" == [yY] ]]; then
    read -rsp "Paste Groq API key (gsk_...): " KEY
    echo ""
    save_key "$KEY"
  else
    echo "Keeping existing key (will still push/restart if enabled)."
  fi
else
  read -rsp "Paste Groq API key (gsk_...): " KEY
  echo ""
  save_key "$KEY"
fi

if [[ "$NO_PUSH" -eq 0 && "$PUSH" -eq 1 ]]; then
  echo ""
  echo "── Push to ${REMOTE_HOST}"
  "$ROOT/scripts/push-env-to-mini.sh" GROQ_API_KEY
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

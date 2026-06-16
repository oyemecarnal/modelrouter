#!/usr/bin/env bash
# Phase 2 connector — Google/Gemini paste-key → local .env → kc-mini (never prints key).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
REMOTE_HOST="${MODELROUTER_REMOTE_HOST:-kc-mini-lan}"
PUSH="${CONNECT_GOOGLE_PUSH:-1}"
RESTART="${CONNECT_GOOGLE_RESTART:-1}"

usage() {
  echo "Usage: connect-google.sh [--no-push] [--no-restart]"
  echo "  Paste Google AI API key (AIza…), save to .env, push to mini, restart gateway."
  echo "  Sets GOOGLE_API_KEY (GEMINI_API_KEY alias synced when empty)."
  echo "  Or set GOOGLE_API_KEY in environment (non-interactive)."
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
  GOOGLE_API_KEY="$1" PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
import os
from pathlib import Path
from modelrouter.env_store import update_env_file, validate_provider_key

key = os.environ.get('GOOGLE_API_KEY', '')
err = validate_provider_key('GOOGLE_API_KEY', key)
if err:
    raise SystemExit(err)
root = Path('''$ENV_FILE''')
update_env_file(root, 'GOOGLE_API_KEY', key)
# LiteLLM may read GEMINI_API_KEY — mirror when unset
lines = root.read_text().splitlines() if root.exists() else []
has_gemini = any(l.startswith('GEMINI_API_KEY=') and l.split('=', 1)[1].strip() for l in lines)
if not has_gemini:
    update_env_file(root, 'GEMINI_API_KEY', key)
print('  ok saved to .env (validated)')
"
}

echo "==> Connect Google AI (ModelRouter connector)"
echo "    Signup: https://aistudio.google.com/apikey"
echo "    Routes: Gemini fallbacks in smart / cheap presets"
echo "    Docs: docs/ENV.md · docs/CONNECTOR_SPEC.md"
echo ""

if [[ -n "${GOOGLE_API_KEY:-}" ]]; then
  KEY="$GOOGLE_API_KEY"
  echo "Using GOOGLE_API_KEY from environment."
  save_key "$KEY"
elif [[ -f "$ENV_FILE" ]] && grep -q '^GOOGLE_API_KEY=.' "$ENV_FILE"; then
  read -rp "GOOGLE_API_KEY already in .env. Replace? [y/N] " REPLACE
  if [[ "$REPLACE" == [yY] ]]; then
    read -rsp "Paste Google AI API key (AIza...): " KEY
    echo ""
    save_key "$KEY"
  else
    echo "Keeping existing key (will still push/restart if enabled)."
  fi
else
  read -rsp "Paste Google AI API key (AIza...): " KEY
  echo ""
  save_key "$KEY"
fi

if [[ "$NO_PUSH" -eq 0 && "$PUSH" -eq 1 ]]; then
  echo ""
  echo "── Push to ${REMOTE_HOST}"
  "$ROOT/scripts/push-env-to-mini.sh" GOOGLE_API_KEY GEMINI_API_KEY
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

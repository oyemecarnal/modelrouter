#!/usr/bin/env bash
# Phase 2 connector — OpenAI paste-key → local .env → kc-mini (never prints key).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
REMOTE_HOST="${MODELROUTER_REMOTE_HOST:-kc-mini-lan}"
PUSH="${CONNECT_OPENAI_PUSH:-1}"
RESTART="${CONNECT_OPENAI_RESTART:-1}"

usage() {
  echo "Usage: connect-openai.sh [--no-push] [--no-restart] [--stash-alt]"
  echo "  Paste OpenAI API key (sk-…), save to .env, push to mini, restart gateway."
  echo "  --stash-alt  move previous OPENAI_API_KEY → OPENAI_API_KEY__ALT_1 when replacing"
  echo "  Or set OPENAI_API_KEY in environment (non-interactive)."
  echo "  Docs: docs/ENV.md"
}

NO_PUSH=0
NO_RESTART=0
STASH_ALT=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-push) NO_PUSH=1; shift ;;
    --no-restart) NO_RESTART=1; shift ;;
    --stash-alt) STASH_ALT=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

save_key() {
  OPENAI_API_KEY="$1" STASH_ALT="$STASH_ALT" PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
import os
from pathlib import Path
from modelrouter.env_store import update_env_file, validate_provider_key

env_path = Path('''$ENV_FILE''')
key = os.environ.get('OPENAI_API_KEY', '')
stash = os.environ.get('STASH_ALT') == '1'
err = validate_provider_key('OPENAI_API_KEY', key)
if err:
    raise SystemExit(err)

old = None
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if line.startswith('OPENAI_API_KEY=') and not line.startswith('OPENAI_API_KEY__'):
            old = line.split('=', 1)[1].strip()
            break

if stash and old and old != key:
    update_env_file(env_path, 'OPENAI_API_KEY__ALT_1', old)
    print('  ok stashed previous key → OPENAI_API_KEY__ALT_1')

update_env_file(env_path, 'OPENAI_API_KEY', key)
print('  ok saved to .env (validated)')
"
  if [[ "$STASH_ALT" -eq 1 ]]; then
    PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -m modelrouter.key_vault ingest-alts 2>/dev/null || true
  fi
}

echo "==> Connect OpenAI (ModelRouter connector)"
echo "    Signup: https://platform.openai.com/api-keys"
echo "    Routes: smart, code, hermes-smart fallbacks"
echo "    Docs: docs/ENV.md · docs/CONNECTOR_SPEC.md"
echo ""

if [[ -n "${OPENAI_API_KEY:-}" ]]; then
  KEY="$OPENAI_API_KEY"
  echo "Using OPENAI_API_KEY from environment."
  save_key "$KEY"
elif [[ -f "$ENV_FILE" ]] && grep -q '^OPENAI_API_KEY=.' "$ENV_FILE"; then
  read -rp "OPENAI_API_KEY already in .env. Replace? [y/N] " REPLACE
  if [[ "$REPLACE" == [yY] ]]; then
    read -rsp "Paste OpenAI API key (sk-...): " KEY
    echo ""
    save_key "$KEY"
  else
    echo "Keeping existing key (will still push/restart if enabled)."
  fi
else
  read -rsp "Paste OpenAI API key (sk-...): " KEY
  echo ""
  save_key "$KEY"
fi

if [[ "$NO_PUSH" -eq 0 && "$PUSH" -eq 1 ]]; then
  echo ""
  echo "── Push to ${REMOTE_HOST}"
  PUSH_KEYS=(OPENAI_API_KEY)
  if grep -q '^OPENAI_API_KEY__ALT_1=.' "$ENV_FILE" 2>/dev/null; then
    PUSH_KEYS+=(OPENAI_API_KEY__ALT_1)
  fi
  # shellcheck disable=SC2068
  "$ROOT/scripts/push-env-to-mini.sh" ${PUSH_KEYS[@]}
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

#!/usr/bin/env bash
# Phase 2 connector — Cohere paste-key → local .env → kc-mini (never prints key).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
REMOTE_HOST="${MODELROUTER_REMOTE_HOST:-kc-mini-lan}"

save_key() {
  COHERE_API_KEY="$1" PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
import os
from pathlib import Path
from modelrouter.env_store import update_env_file, validate_provider_key
key = os.environ.get('COHERE_API_KEY', '')
err = validate_provider_key('COHERE_API_KEY', key)
if err: raise SystemExit(err)
update_env_file(Path('''$ENV_FILE'''), 'COHERE_API_KEY', key)
print('  ok saved to .env (validated)')
"
}

echo "==> Connect Cohere (ModelRouter connector)"
echo "    Signup: https://dashboard.cohere.com"
read -rsp "Paste Cohere API key: " KEY
echo ""
save_key "$KEY"
"$ROOT/scripts/push-env-to-mini.sh" COHERE_API_KEY
ssh -o ConnectTimeout=5 "$REMOTE_HOST" 'cd ~/dev/modelrouter && make restart' 2>/dev/null || true
echo "==> Done."

#!/usr/bin/env bash
# Export vault → laptop .env → push __ALT_N keys to kc-mini.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env

RESTART_MINI=0
for arg in "$@"; do
  case "$arg" in
    --restart-mini) RESTART_MINI=1 ;;
  esac
done

echo "==> Vault sync alts (export + push to mini)"
echo ""

"$ROOT/scripts/check-alt-keys.sh" || true
echo ""

PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
from collections import Counter
from modelrouter.key_vault import load_vault, load_vault_config
doc = load_vault()
cfg = load_vault_config()
counts = Counter(r['env_var'] for r in doc.get('keys') or [] if r.get('enabled'))
need = {'GROQ_API_KEY', 'OPENAI_API_KEY', 'MISTRAL_API_KEY', 'ANTHROPIC_API_KEY'}
multi = [v for v in sorted(need) if counts.get(v, 0) >= 2]
if not multi:
    print('[vault-sync-alts] Vault has <2 keys per provider — add second keys:')
    print('  1. Paste alt into .env as VAR__ALT_1=... (connect scripts) or second host .env')
    print('  2. make vault-scrape-collect')
    print('  3. Re-run: make vault-sync-alts')
else:
    print('[vault-sync-alts] Multi-key providers:', ', '.join(f'{v}({counts[v]})' for v in multi))
"

echo ""
"$ROOT/scripts/vault-export.sh"
echo ""
"$ROOT/scripts/push-alt-keys-mini.sh"
echo ""
"$ROOT/scripts/check-alt-keys-mini.sh" || true

if [[ "$RESTART_MINI" -eq 1 ]]; then
  REMOTE_HOST="${MODELROUTER_REMOTE_HOST:-kc-mini-lan}"
  REMOTE_DIR="${MODELROUTER_REMOTE_DIR:-$HOME/dev/modelrouter}"
  echo "[vault-sync-alts] Restarting mini gateway..."
  ssh -o ConnectTimeout=8 "$REMOTE_HOST" "cd '${REMOTE_DIR}' && make restart"
fi

echo ""
echo "[vault-sync-alts] Done"

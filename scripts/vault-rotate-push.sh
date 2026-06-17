#!/usr/bin/env bash
# Apply last 429 rotate hint → export .env → push rotated keys to kc-mini
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
  esac
done

if [[ "$DRY" == 1 ]]; then
  "$ROOT/scripts/vault-rotate-export.sh" --dry-run
  echo "[vault-rotate-push] dry-run — would push keys from last rotate hint"
  PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
import json
from pathlib import Path
from modelrouter.key_vault import rotate_hints_path, load_vault_config
p = rotate_hints_path(load_vault_config())
rows = json.loads(p.read_text()) if p.exists() else []
last = next((h for h in reversed(rows) if h.get('ok')), {})
env_var = last.get('env_var') or 'GROQ_API_KEY'
keys = [env_var]
root = Path('$ROOT')
env = root / '.env'
if env.exists():
    for line in env.read_text().splitlines():
        if line.startswith(f'{env_var}__ALT_'):
            keys.append(line.split('=', 1)[0])
print('Would push:', ' '.join(keys))
"
  exit 0
fi

"$ROOT/scripts/vault-rotate-export.sh"

PUSH_KEYS="$(PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
import json
from pathlib import Path
from modelrouter.key_vault import rotate_hints_path, load_vault_config
p = rotate_hints_path(load_vault_config())
rows = json.loads(p.read_text()) if p.exists() else []
last = next((h for h in reversed(rows) if h.get('ok')), {})
env_var = last.get('env_var') or 'GROQ_API_KEY'
keys = [env_var]
root = Path('$ROOT')
env = root / '.env'
if env.exists():
    for line in env.read_text().splitlines():
        if line.startswith(f'{env_var}__ALT_'):
            keys.append(line.split('=', 1)[0])
print(' '.join(keys))
")"

if [[ -z "$PUSH_KEYS" ]]; then
  echo "[vault-rotate-push] No keys to push" >&2
  exit 1
fi

# shellcheck disable=SC2086
"$ROOT/scripts/push-env-to-mini.sh" $PUSH_KEYS
PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
from modelrouter.key_vault import mark_rotate_hint_applied
ok = mark_rotate_hint_applied()
print('[vault-rotate-push] marked hint applied' if ok else '[vault-rotate-push] no pending hint to clear')
"
echo "[vault-rotate-push] Done — restart mini gateway if needed: ssh kc-mini-lan 'cd ~/dev/modelrouter && make restart'"

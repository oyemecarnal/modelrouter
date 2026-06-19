#!/usr/bin/env bash
# Apply last 429 rotate hint → vault export merge into .env
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
  esac
done

PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
import json, sys
from modelrouter.key_vault import apply_last_rotate_export

dry = bool(int('${DRY}'))
result = apply_last_rotate_export(dry_run=dry, overwrite=True)
print(json.dumps({k: v for k, v in result.items() if k != 'keys'}, indent=2))
if result.get('dry_run') and result.get('keys'):
    print('Would write:')
    for k, fp in sorted(result['keys'].items()):
        print(f'  {k}: {fp}')
sys.exit(0 if result.get('ok') else 1)
"

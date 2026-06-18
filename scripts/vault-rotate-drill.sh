#!/usr/bin/env bash
# Dry-run 429 rotate pipeline readiness (no secrets printed).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env

ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; exit 1; }

echo "==> 429 rotate drill (dry-run)"
echo ""

"$ROOT/scripts/check-alt-keys.sh" || true
echo ""
"$ROOT/scripts/check-alt-keys-mini.sh" || true
echo ""

PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
from modelrouter.key_vault import vault_alt_readiness, rotate_hints_path, load_vault_config
import json
r = vault_alt_readiness()
for var, n in r['counts'].items():
    mark = 'ok' if r['ready'][var] else 'missing'
    print(f'  vault {var}: {n} key(s) [{mark}]')
if r['missing']:
    print('  ! shuffle inactive until 2+ keys:', ', '.join(r['missing']))
else:
    print('  ok all alt-route providers have 2+ vault keys')
path = rotate_hints_path(load_vault_config())
hints = []
if path.exists():
    try:
        hints = json.loads(path.read_text())
    except json.JSONDecodeError:
        pass
pending = [h for h in hints if h.get('ok') and not h.get('applied_at')]
print(f'  rotate hints: {len(hints)} total, {len(pending)} pending')
"

echo ""
echo "── Mini auto-rotate gates"
if "$ROOT/scripts/enable-auto-rotate-mini.sh" 2>/dev/null; then
  ok "mini auto-rotate status"
else
  warn "mini auto-rotate status skipped (SSH)"
fi

echo ""
echo "── Dry-run export/push"
if "$ROOT/scripts/vault-rotate-export.sh" --dry-run 2>/dev/null; then
  ok "vault-rotate-export dry-run"
else
  warn "no pending rotate hint — export dry-run skipped (expected without 429)"
fi

if "$ROOT/scripts/vault-rotate-push.sh" --dry-run 2>/dev/null; then
  ok "vault-rotate-push dry-run"
else
  warn "vault-rotate-push dry-run skipped"
fi

echo ""
echo "── Auto gates (opt-in on gateway host)"
for gate in MODELROUTER_AUTO_VAULT_ROTATE MODELROUTER_AUTO_VAULT_RESTART MODELROUTER_AUTO_VAULT_PUSH; do
  if [[ "${!gate:-}" == "1" ]]; then
    ok "${gate}=1"
  else
    warn "${gate} unset — manual rotate path only"
  fi
done

echo ""
echo "  Human path when 2+ keys exist:"
echo "    make connect-alt-key PROVIDER=groq"
echo "    make vault-bootstrap-alts"
echo "    make enable-auto-rotate-mini --enable"
echo ""
echo "── 429 simulate (groq, cleanup)"
if "$ROOT/scripts/vault-rotate-simulate.sh" groq --cleanup 2>/dev/null; then
  ok "vault-rotate-simulate groq"
else
  warn "vault-rotate-simulate skipped (need 2+ keys per provider)"
fi

echo ""
ok "rotate drill complete (dry-run only)"

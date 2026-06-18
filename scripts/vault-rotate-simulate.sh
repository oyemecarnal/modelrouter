#!/usr/bin/env bash
# Simulate provider 429 → vault rotate hint + export dry-run (no gateway call).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_activate

PROVIDER="${1:-groq}"
CLEANUP=0
for arg in "$@"; do
  case "$arg" in
    --cleanup) CLEANUP=1 ;;
  esac
done

ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; exit 1; }

echo "==> 429 rotate simulate (${PROVIDER})"
echo ""

PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" - "$PROVIDER" "$CLEANUP" <<'PY'
import json, sys
from modelrouter.key_vault import (
    apply_last_rotate_export,
    env_var_for_model,
    mark_rotate_hint_applied,
    record_rate_limit,
    vault_alt_readiness,
)

provider = sys.argv[1]
cleanup = sys.argv[2] == "1"
models = {
    "groq": "groq/llama-3.3-70b",
    "anthropic": "anthropic/claude-sonnet-4-20250514",
    "openai": "openai/gpt-4o",
    "mistral": "mistral/mistral-small",
}
model = models.get(provider)
if not model:
    raise SystemExit(f"unknown provider: {provider} (groq|anthropic|openai|mistral)")

env_var = env_var_for_model(model)
ready = vault_alt_readiness()
if not env_var or not ready["ready"].get(env_var):
    counts = ready["counts"].get(env_var or "", 0)
    raise SystemExit(f"{env_var or provider} needs 2+ vault keys (have {counts})")

hint = record_rate_limit(model, "HTTP 429 Too Many Requests")
print(json.dumps({"rotate_hint": {k: hint.get(k) for k in ("ok", "env_var", "next_fingerprint", "model")}}, indent=2))
if not hint.get("ok"):
    raise SystemExit(f"record_rate_limit failed: {hint}")

export = apply_last_rotate_export(dry_run=True, overwrite=True)
print(json.dumps({"export_dry_run": {k: export.get(k) for k in ("ok", "target", "keys") if k in export}}, indent=2))
if export.get("keys"):
    print("Would export fingerprints:")
    for k, fp in sorted(export["keys"].items()):
        if env_var in k:
            print(f"  {k}: {fp}")

if cleanup:
    cleared = mark_rotate_hint_applied()
    print(json.dumps({"cleanup": "hint marked applied" if cleared else "no hint cleared"}, indent=2))
else:
    print("Note: rotate hint left pending — run: make vault-rotate-export or re-run with --cleanup")
PY

echo ""
ok "429 rotate simulate complete"

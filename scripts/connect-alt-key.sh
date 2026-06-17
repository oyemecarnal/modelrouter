#!/usr/bin/env bash
# Paste alternate API key → VAR__ALT_N in .env (never prints value).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
PUSH="${CONNECT_ALT_PUSH:-1}"
SLOT="${ALT_SLOT:-1}"

usage() {
  echo "Usage: connect-alt-key.sh PROVIDER [--slot N] [--no-push]"
  echo "  Providers: groq, anthropic, openai, mistral"
  echo "  Writes GROQ_API_KEY__ALT_1 etc., then optional push-alt-keys-mini."
  echo "  Or: PROVIDER=groq make connect-alt-key"
}

NO_PUSH=0
PROVIDER=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --slot=*) SLOT="${1#*=}"; shift ;;
    --slot) SLOT="${2:?}"; shift 2 ;;
    --no-push) NO_PUSH=1; shift ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; usage; exit 1 ;;
    *)
      if [[ -z "$PROVIDER" ]]; then
        PROVIDER="$1"
      else
        echo "Unexpected arg: $1" >&2
        usage
        exit 1
      fi
      shift
      ;;
  esac
done

PROVIDER="${PROVIDER:-${PROVIDER_ID:-}}"
[[ -n "$PROVIDER" ]] || { usage; exit 1; }

export ROOT
PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" - "$PROVIDER" "$SLOT" "$ENV_FILE" <<'PY'
import os, sys
from pathlib import Path
import yaml

provider, slot_s, env_path = sys.argv[1], sys.argv[2], Path(sys.argv[3])
root = Path(os.environ["ROOT"])
slot = int(slot_s)
if slot < 1 or slot > 9:
    raise SystemExit("slot must be 1-9")

cfg = yaml.safe_load((root / "config/connectors.yaml").read_text()) or {}
conn = (cfg.get("connectors") or {}).get(provider)
if not conn:
    raise SystemExit(f"unknown provider: {provider}")

base = conn.get("env") or ""
if not base:
    raise SystemExit(f"connector {provider} missing env var")

alt_key = f"{base}__ALT_{slot}"
val = os.environ.get(base) or os.environ.get(alt_key) or ""
if not val:
    val = input(f"Paste {provider} alt key ({alt_key}): ").strip()

from modelrouter.env_store import update_env_file, validate_provider_key
err = validate_provider_key(base, val)
if err:
    raise SystemExit(err)

update_env_file(env_path, alt_key, val)
print(f"  ok saved {alt_key} to .env (validated)")
PY

if [[ "$NO_PUSH" -eq 0 && "$PUSH" -eq 1 ]]; then
  "$ROOT/scripts/push-alt-keys-mini.sh" || true
fi

echo "  Next: make vault-scrape-collect && make vault-sync-alts"

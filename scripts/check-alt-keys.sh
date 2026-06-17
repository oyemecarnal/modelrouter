#!/usr/bin/env bash
# Report LiteLLM __ALT_N env vars referenced in config vs .env (never prints values).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env

STRICT=0
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
  esac
done

ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; exit 1; }

ALT_VARS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && ALT_VARS+=("$line")
done < <(
  grep -ohE 'os\.environ/[A-Z0-9_]+__ALT_[0-9]+' \
    "$ROOT/config/modelrouter.yaml" "$ROOT/config/modelrouter.minimal.yaml" 2>/dev/null \
    | sed 's|os.environ/||' | sort -u
)

if [[ "${#ALT_VARS[@]}" -eq 0 ]]; then
  ok "no __ALT_N routes in config"
  exit 0
fi

echo "==> Alt key check (${#ALT_VARS[@]} env vars in LiteLLM config)"
ENV_FILE="${ROOT}/.env"
missing=0
present=0

for var in "${ALT_VARS[@]}"; do
  if [[ -f "$ENV_FILE" ]] && grep -q "^${var}=" "$ENV_FILE"; then
    val="$(grep "^${var}=" "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '[:space:]')"
    if [[ -n "$val" && "$val" != "changeme" && "$val" != "REPLACE_ME" ]]; then
      ok "${var} set"
      present=$((present + 1))
      continue
    fi
  fi
  warn "${var} missing — run: make vault-scrape-collect && make vault-export (need 2+ keys per provider)"
  missing=$((missing + 1))
done

echo ""
if [[ "$present" -eq 0 ]]; then
  warn "No __ALT_N keys exported — alt routes inactive (primary keys still work)"
elif [[ "$missing" -gt 0 ]]; then
  warn "${missing} alt var(s) missing — shuffle may skip those deployments"
else
  ok "all alt keys present locally"
fi

if [[ "$STRICT" -eq 1 && "$missing" -gt 0 ]]; then
  fail "strict mode: missing ${missing} alt key(s)"
fi

exit 0

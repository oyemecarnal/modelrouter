#!/usr/bin/env bash
# Check __ALT_N vars on kc-mini .env (names only, never values).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env
REMOTE_HOST="$(modelrouter_remote_host)"
REMOTE_DIR="${MODELROUTER_REMOTE_DIR:-$HOME/dev/modelrouter}"

ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

ALT_VARS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && ALT_VARS+=("$line")
done < <(
  grep -ohE 'os\.environ/[A-Z0-9_]+__ALT_[0-9]+' \
    "$ROOT/config/modelrouter.yaml" "$ROOT/config/modelrouter.minimal.yaml" 2>/dev/null \
    | sed 's|os.environ/||' | sort -u
)

echo "==> Alt key check (kc-mini)"
echo "    Host: ${REMOTE_HOST}:${REMOTE_DIR}/.env"
echo ""

if [[ "${#ALT_VARS[@]}" -eq 0 ]]; then
  ok "no __ALT_N routes in config"
  exit 0
fi

REMOTE_NAMES="$(ssh -o ConnectTimeout=8 "$REMOTE_HOST" \
  "grep -E '^[A-Z0-9_]+__ALT_[0-9]+=' '${REMOTE_DIR}/.env' 2>/dev/null | cut -d= -f1 | sort -u" 2>/dev/null || true)"

missing=0
present=0
for var in "${ALT_VARS[@]}"; do
  if echo "$REMOTE_NAMES" | grep -qx "$var"; then
    ok "${var} on mini"
    present=$((present + 1))
  else
    warn "${var} missing on mini — run: make vault-sync-alts"
    missing=$((missing + 1))
  fi
done

echo ""
if [[ "$present" -eq 0 ]]; then
  warn "No __ALT_N keys on mini — alt routes inactive (primary keys still work)"
elif [[ "$missing" -gt 0 ]]; then
  warn "${missing} alt var(s) missing on mini"
else
  ok "all alt keys present on mini"
fi

exit 0

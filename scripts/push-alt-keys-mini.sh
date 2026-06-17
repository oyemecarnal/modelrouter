#!/usr/bin/env bash
# Push __ALT_N keys from laptop .env → kc-mini (after make vault-export).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env

ALT_VARS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && ALT_VARS+=("$line")
done < <(
  grep -ohE 'os\.environ/[A-Z0-9_]+__ALT_[0-9]+' \
    "$ROOT/config/modelrouter.yaml" "$ROOT/config/modelrouter.minimal.yaml" 2>/dev/null \
    | sed 's|os.environ/||' | sort -u
)

if [[ "${#ALT_VARS[@]}" -eq 0 ]]; then
  echo "[push-alt-keys-mini] No __ALT_N routes in config"
  exit 0
fi

PUSH=()
for var in "${ALT_VARS[@]}"; do
  if grep -q "^${var}=" "$ROOT/.env" 2>/dev/null; then
    val="$(grep "^${var}=" "$ROOT/.env" | head -1 | cut -d= -f2- | tr -d '[:space:]')"
    [[ -n "$val" ]] && PUSH+=("$var")
  fi
done

if [[ "${#PUSH[@]}" -eq 0 ]]; then
  echo "[push-alt-keys-mini] No alt keys in local .env — run: make vault-scrape-collect && make vault-export"
  exit 0
fi

echo "[push-alt-keys-mini] Pushing ${#PUSH[@]} alt key(s) to kc-mini"
# shellcheck disable=SC2086
"$ROOT/scripts/push-env-to-mini.sh" "${PUSH[@]}"
echo "[push-alt-keys-mini] Restart mini gateway: ssh kc-mini-lan 'cd ~/dev/modelrouter && make restart'"

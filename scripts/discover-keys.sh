#!/usr/bin/env bash
# Audit API keys across known locations (masked output only).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/lib.sh" 2>/dev/null || MODELROUTER_ROOT="$ROOT"

mask() {
  local v="$1"
  [[ -z "$v" ]] && { echo "(empty)"; return; }
  [[ "$v" == op://* ]] && { echo "$v"; return; }
  [[ ${#v} -le 8 ]] && { echo "***"; return; }
  echo "${v:0:4}…${v: -4}"
}

scan_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  echo ""
  echo "── $f"
  while IFS= read -r line; do
    line="${line#export }"
    [[ "$line" =~ ^# ]] && continue
    [[ "$line" != *"="* ]] && continue
    local k="${line%%=*}"
    local v="${line#*=}"
    v="${v%\"}"; v="${v#\"}"; v="${v%\'}"; v="${v#\'}"
    [[ "$k" =~ (KEY|TOKEN|SECRET|PASSWORD|API_) ]] || continue
    printf "  %-32s %s\n" "$k" "$(mask "$v")"
  done < <(grep -E '^[[:space:]]*(export[[:space:]]+)?[A-Z_]*(KEY|TOKEN|SECRET|PASSWORD|API_|_API)' "$f" 2>/dev/null || true)
}

echo "==> ModelRouter API key audit"
echo "    Host: $(hostname -s 2>/dev/null || hostname)"

LOCAL_SOURCES=(
  "$HOME/.zshrc"
  "$HOME/.bash_profile"
  "$HOME/dev/smalshi/.env"
  "$HOME/dev/smalshi/Codex/.env"
  "$HOME/dev/coinbot/.env"
  "$HOME/dev/Kalshi_bot/.env"
  "$HOME/dev/project_kc/signals/.env"
  "$HOME/dev/openclaw/.env"
  "$ROOT/.env"
  "$ROOT/secrets.yaml"
)

for f in "${LOCAL_SOURCES[@]}"; do
  scan_file "$f"
done

if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new kc-mini-lan 'true' 2>/dev/null; then
  echo ""
  echo "── kc-mini (always-on)"
  ssh kc-mini-lan 'for f in ~/dev/smalshi/.env ~/dev/coinbot/.env ~/dev/modelrouter/.env ~/dev/Kalshi_bot/.env ~/dev/openclaw/.env; do
    [ -f "$f" ] || continue
    echo "── $f"
    grep -E "^[A-Z_]*(KEY|TOKEN|SECRET|PASSWORD)=" "$f" 2>/dev/null | sed -E "s/=(.*)/=***MASKED***/"
  done'
else
  echo ""
  echo "── kc-mini: unreachable (skip remote audit)"
fi

echo ""
echo "Network vault: make vault-scrape          # masked discovery"
echo "               make vault-scrape-collect  # ingest (see config/key_vault.yaml)"
echo "Full machine scan (allowed paths + crypto surfaces): make inventory"
echo "Run: ./scripts/sync-keys.sh --dry-run   # preview fill for modelrouter/.env"
echo "Run: ./scripts/sync-keys.sh             # fill empty vars only"

#!/usr/bin/env bash
# Remove stray LLM provider keys from tower agent env files (CLEAN_WIRES Option A).
# Strips coinbot and other ~/dev/*/.env* — never prints key values. Exchange keys untouched.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh" 2>/dev/null || true

PROVIDER_VARS=(
  GROQ_API_KEY
  ANTHROPIC_API_KEY
  OPENAI_API_KEY
  MISTRAL_API_KEY
  GOOGLE_API_KEY
  GEMINI_API_KEY
  OPENROUTER_API_KEY
  DEEPSEEK_API_KEY
  TOGETHER_API_KEY
  FIREWORKS_API_KEY
  COHERE_API_KEY
)

ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; }

tower_ssh_host() {
  if [[ -n "${KC_TOWER_SSH:-}" ]]; then
    echo "$KC_TOWER_SSH"
    return 0
  fi
  local candidate
  for candidate in gateway-tower kc-tower kc-tower-lan; do
    if ssh -o ConnectTimeout=4 -o BatchMode=yes "$candidate" 'true' 2>/dev/null; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

echo "==> Strip tower LLM keys (provider keys → kc-mini only)"
echo "    Spec: docs/TOWER_CLEANUP.md · docs/WHY_MODELROUTER.md"
echo ""

if ! host="$(tower_ssh_host)"; then
  warn "kc-tower SSH unreachable — skip (set KC_TOWER_SSH when online)"
  exit 0
fi
ok "kc-tower SSH (${host})"

vars_csv="$(IFS=,; echo "${PROVIDER_VARS[*]}")"

REMOTE_SCRIPT='set -euo pipefail
IFS=, read -r -a vars <<<"'"$vars_csv"'"
removed=0
scan_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  local base changed=0
  base="$(basename "$f")"
  case "$base" in
    .env.example|.env.local.example|.env.sample) return 0 ;;
  esac
  [[ "$base" == *".bak"* ]] && return 0
  cp "$f" "${f}.bak.$(date +%Y%m%d%H%M)" 2>/dev/null || true
  for v in "${vars[@]}"; do
    if grep -q "^${v}=" "$f" 2>/dev/null; then
      sed -i "/^${v}=/d" "$f"
      echo "STRIPPED:${f}:${v}"
      removed=$((removed + 1))
      changed=1
    fi
  done
  if [[ "$changed" -eq 1 && "$f" == *coinbot* ]]; then
    if ! grep -q "^# LLM via gateway" "$f" 2>/dev/null; then
      echo "# LLM via gateway — source ~/.config/modelrouter/client.env" >> "$f"
    fi
  fi
}
while IFS= read -r -d "" d; do
  for f in "$d"/.env "$d"/.env.local "$d"/.env.*; do
    scan_file "$f"
  done
done < <(find "$HOME/dev" -maxdepth 3 -type d -print0 2>/dev/null || true)
echo "REMOVED:${removed}"
'

out="$(ssh -o ConnectTimeout=8 "$host" "bash -s" <<<"$REMOTE_SCRIPT" 2>/dev/null)" || {
  fail "remote strip failed"
  exit 1
}

stripped=0
while IFS= read -r line; do
  case "$line" in
    STRIPPED:*)
      path="${line#STRIPPED:}"
      var="${path##*:}"
      file="${path%:*}"
      ok "removed ${var} from ${file}"
      stripped=$((stripped + 1))
      ;;
    REMOVED:*)
      ;;
  esac
done <<<"$out"

if [[ "$stripped" -eq 0 ]]; then
  ok "no LLM provider keys found in tower agent env files"
else
  ok "stripped ${stripped} provider key(s)"
  warn "ensure agents source ~/.config/modelrouter/client.env for LLM calls"
fi

echo ""
echo "── Re-audit"
exec "$ROOT/scripts/audit-tower-wires.sh"

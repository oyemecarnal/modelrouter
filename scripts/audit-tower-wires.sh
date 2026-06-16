#!/usr/bin/env bash
# Audit kc-tower for stray provider API keys (CLEAN_WIRES) — never prints values.
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
  for candidate in kc-tower kc-tower-lan; do
    if ssh -o ConnectTimeout=4 -o BatchMode=yes "$candidate" 'true' 2>/dev/null; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

echo "==> Tower wire audit (provider keys must live on kc-mini only)"
echo "    Spec: docs/CLEAN_WIRES.md"
echo ""

if ! host="$(tower_ssh_host)"; then
  warn "kc-tower SSH unreachable — skip audit (set KC_TOWER_SSH when online)"
  exit 0
fi
ok "kc-tower SSH (${host})"

# Remote: scan common env files; print only path + var name when set.
REMOTE_SCRIPT='set -euo pipefail
vars="'"${PROVIDER_VARS[*]}"'"
paths=(
  "$HOME/.env"
  "$HOME/.bashrc"
  "$HOME/.zshrc"
  "$HOME/.profile"
  "$HOME/.config/modelrouter/client.env"
)
while IFS= read -r -d "" d; do
  for f in "$d"/.env "$d"/.env.local; do
    [[ -f "$f" ]] && paths+=("$f")
  done
done < <(find "$HOME/dev" -maxdepth 3 -type d -print0 2>/dev/null || true)

hits=0
for f in "${paths[@]}"; do
  [[ -f "$f" ]] || continue
  for v in $vars; do
    if grep -q "^${v}=" "$f" 2>/dev/null; then
      line=$(grep "^${v}=" "$f" | head -1)
      val="${line#*=}"
      if [[ -n "$val" && "$val" != *change-me* && "$val" != *placeholder* ]]; then
        # client.env uses OPENAI_API_KEY as gateway auth shim (not vendor key)
        if [[ "$f" == *client.env && "$v" == OPENAI_API_KEY ]]; then
          continue
        fi
        echo "STRAY:${f}:${v}"
        hits=$((hits + 1))
      fi
    fi
  done
done
echo "HITS:${hits}"
'

out="$(ssh -o ConnectTimeout=8 "$host" "bash -s" <<<"$REMOTE_SCRIPT" 2>/dev/null)" || {
  fail "tower audit failed"
  exit 1
}

strays=0
while IFS= read -r line; do
  case "$line" in
    STRAY:*)
      path="${line#STRAY:}"
      var="${path##*:}"
      file="${path%:*}"
      fail "stray ${var} in ${file}"
      if [[ "$file" == *coinbot* ]]; then
        warn "coinbot: remove ${var} from .env; use source ~/.config/modelrouter/client.env"
      fi
      strays=$((strays + 1))
      ;;
    HITS:*)
      total="${line#HITS:}"
      ;;
  esac
done <<<"$out"

if [[ "${total:-0}" -eq 0 ]]; then
  ok "no provider keys found on tower agent paths"
  if ssh -o ConnectTimeout=5 "$host" 'test -f ~/.config/modelrouter/client.env' 2>/dev/null; then
    ok "client.env present (gateway auth only)"
  else
    warn "client.env missing — run: make push-client-env-tower"
  fi
  echo ""
  echo "Tower wires OK"
  exit 0
fi

echo ""
echo "Action: remove provider keys from tower; use gateway presets via client.env"
echo "  make clean-tower-wires && make smoke-tower"
echo "  docs/TOWER_CLEANUP.md  (coinbot and other agent .env files)"
exit 1

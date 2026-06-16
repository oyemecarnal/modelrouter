#!/usr/bin/env bash
# Key hygiene checks — no secret values printed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env

ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; }

issues=0

echo "==> Key hygiene (laptop)"

MASTER="${MODELROUTER_MASTER_KEY:-}"
SALT="${LITELLM_SALT_KEY:-}"

if [[ -z "$MASTER" || "$MASTER" == *change-me* ]]; then
  warn "MODELROUTER_MASTER_KEY placeholder"
  issues=$((issues + 1))
else
  ok "MODELROUTER_MASTER_KEY set"
fi

if [[ -z "$SALT" || "$SALT" == *change-me* ]]; then
  warn "LITELLM_SALT_KEY placeholder — run: make rotate-salt-key"
  issues=$((issues + 1))
elif [[ "$SALT" == "$MASTER" ]]; then
  warn "LITELLM_SALT_KEY equals master — run: make rotate-salt-key"
  issues=$((issues + 1))
else
  ok "LITELLM_SALT_KEY distinct from master"
fi

for k in GROQ_API_KEY ANTHROPIC_API_KEY OPENAI_API_KEY MISTRAL_API_KEY GOOGLE_API_KEY; do
  v="${!k:-}"
  if [[ -n "$v" ]]; then ok "$k set on laptop"
  else warn "$k empty on laptop"
  fi
done

# Groq rotation waived unless you choose to rotate — see docs/KEY_ROTATION.md

echo ""
echo "── kc-mini (remote)"
if ssh -o ConnectTimeout=4 kc-mini-lan 'test -d ~/dev/modelrouter' 2>/dev/null; then
  ssh -o ConnectTimeout=4 kc-mini-lan 'cd ~/dev/modelrouter && source .env 2>/dev/null; \
    for k in GROQ_API_KEY ANTHROPIC_API_KEY OPENAI_API_KEY MISTRAL_API_KEY GOOGLE_API_KEY LITELLM_SALT_KEY MODELROUTER_MASTER_KEY; do \
      eval v=\$${k}; \
      if [[ -n "$v" && "$v" != *change-me* ]]; then echo "  ok $k"; else echo "  ! $k missing/placeholder"; fi; \
    done; \
    if [[ -n "${LITELLM_SALT_KEY:-}" && -n "${MODELROUTER_MASTER_KEY:-}" && "$LITELLM_SALT_KEY" == "$MODELROUTER_MASTER_KEY" ]]; then \
      echo "  ! LITELLM_SALT_KEY equals master on mini"; fi' 2>/dev/null || warn "mini .env check failed"
else
  warn "kc-mini-lan unreachable"
  issues=$((issues + 1))
fi

echo ""
if [[ $issues -gt 0 ]]; then
  echo "Action: make rotate-salt-key && make push-env-mini (after Groq/Anthropic/OpenAI updates)"
  exit 1
fi
echo "Key hygiene OK"
echo "  Optional: make audit-tower-wires  # stray provider keys on kc-tower"

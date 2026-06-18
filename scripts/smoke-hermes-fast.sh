#!/usr/bin/env bash
# Smoke-test hermes-fast preset via kc-mini gateway (Groq route).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env

GW="${GW:-$(modelrouter_gateway_url)}"
KEY="${MODELROUTER_KEY_HERMES:-${MODELROUTER_MASTER_KEY:-}}"
BASE="${GW}/v1"

ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; exit 1; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

echo "==> Hermes-fast smoke (Groq route)"
echo "    Gateway: ${BASE}"
echo ""

[[ -n "$KEY" ]] || fail "MODELROUTER_KEY_HERMES or MODELROUTER_MASTER_KEY required"

if [[ -z "${GROQ_API_KEY:-}" ]]; then
  warn "GROQ_API_KEY not in local env — mini must have key for Groq backend"
else
  ok "GROQ_API_KEY present locally"
fi

if curl -sf --max-time 4 "${GW}/health/liveliness" &>/dev/null; then
  ok "kc-mini gateway alive (${GW})"
else
  fail "kc-mini gateway down at ${GW} — run: make bootstrap-mini or make doctor-fix"
fi

models_json="$(curl -sf --max-time 8 "${BASE}/models" -H "Authorization: Bearer ${KEY}" 2>/dev/null || true)"
if [[ -n "$models_json" ]] && echo "$models_json" | grep -q '"hermes-fast"'; then
  ok "hermes-fast in /v1/models"
else
  fail "hermes-fast missing from /v1/models — deploy config: make deploy-mini"
fi

if grep -q "^GROQ_API_KEY__ALT_1=" "$ROOT/.env" 2>/dev/null; then
  ok "GROQ_API_KEY__ALT_1 present locally (alt shuffle active when on mini)"
else
  warn "GROQ_API_KEY__ALT_1 not local — stash old key: make connect-groq --stash-alt"
fi

body='{"model":"hermes-fast","messages":[{"role":"user","content":"Reply with exactly: pong"}],"max_tokens":16}'
if curl -sf --max-time 60 "${BASE}/chat/completions" \
  -H "Authorization: Bearer ${KEY}" \
  -H "Content-Type: application/json" \
  -d "$body" >/dev/null; then
  ok "hermes-fast chat OK"
else
  fail "hermes-fast chat failed — check GROQ_API_KEY on mini and gateway logs"
fi

echo ""
echo "  Optional: make connect-groq  ·  docs/ENV.md"

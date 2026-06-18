#!/usr/bin/env bash
# Smoke-test tower → kc-mini gateway path (hermes-fast / cheap presets).
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

run_curl_smoke() {
  local where="$1"
  local runner="$2"  # "local" or ssh host

  smoke_preset() {
    local preset="$1"
    local body
    body=$(printf '{"model":"%s","messages":[{"role":"user","content":"ping"}],"max_tokens":8}' "$preset")
    if [[ "$runner" == "local" ]]; then
      curl -sf "${BASE}/chat/completions" \
        -H "Authorization: Bearer ${KEY}" \
        -H "Content-Type: application/json" \
        -d "$body" >/dev/null
    else
      ssh -o ConnectTimeout=8 "$runner" \
        "curl -sf '${BASE}/chat/completions' -H 'Authorization: Bearer ${KEY}' -H 'Content-Type: application/json' -d '${body}'" >/dev/null
    fi
  }

  for preset in hermes-fast cheap; do
    if smoke_preset "$preset"; then
      ok "${where}: ${preset} chat OK"
    else
      fail "${where}: ${preset} chat failed"
    fi
  done
}

echo "==> Tower gateway smoke"
echo "    Gateway: ${BASE}"
echo ""

[[ -n "$KEY" ]] || fail "MODELROUTER_KEY_HERMES or MODELROUTER_MASTER_KEY required"

if curl -sf --max-time 4 "${GW}/health/liveliness" &>/dev/null; then
  ok "kc-mini gateway alive (${GW})"
else
  fail "kc-mini gateway down at ${GW}"
fi

if host="$(tower_ssh_host)"; then
  ok "kc-tower SSH (${host})"
  if ssh -o ConnectTimeout=5 "$host" "test -f ~/.config/modelrouter/client.env"; then
    ok "tower client.env present"
  else
    warn "tower client.env missing — run: make push-client-env-tower"
  fi
  run_curl_smoke "tower" "$host"
else
  warn "kc-tower SSH unreachable — simulating tower path from laptop"
  run_curl_smoke "laptop→mini (LAN)" "local"
  echo ""
  echo "  When tower is online: make push-client-env-tower && make smoke-tower"
fi

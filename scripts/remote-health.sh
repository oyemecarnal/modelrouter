#!/usr/bin/env bash
# Ping ModelRouter health on laptop + gateway-mini (+ optional tower SSH).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env

check_url() {
  local name="$1" url="$2"
  if curl -sf --max-time 4 "${url}/health/liveliness" &>/dev/null; then
    echo "  ok  $name  $url"
    return 0
  fi
  echo "  down $name  $url"
  return 1
}

_probe_liveness() {
  curl -sf --max-time 4 "${1}/health/liveliness" &>/dev/null
}

mini_gateway_urls() {
  modelrouter_mini_gateway_urls
}

check_mini_gateway() {
  local url tried=""
  while IFS= read -r url; do
    tried="${tried}${tried:+ }${url}"
    if _probe_liveness "$url"; then
      echo "  ok  gateway-mini  $url"
      MINI_GATEWAY_URL="$url"
      return 0
    fi
  done < <(mini_gateway_urls)
  echo "  down gateway-mini  (tried:${tried})"
  return 1
}

tower_ssh_host() {
  if [[ -n "${KC_TOWER_SSH:-}" ]]; then
    echo "$KC_TOWER_SSH"
    return 0
  fi
  local candidate
  for candidate in gateway-tower kc-tower kc-tower-lan; do
    if ssh -o ConnectTimeout=3 -o BatchMode=yes "$candidate" 'true' 2>/dev/null; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

echo "==> Remote health"
fail=0
MINI_GATEWAY_URL=""

check_url "laptop" "http://127.0.0.1:${MODELROUTER_PORT:-3000}" || fail=1
check_mini_gateway || fail=1

if host="$(tower_ssh_host)"; then
  echo "  ok  gateway-tower  ssh $host"
  # Linux runtime hosts cannot resolve mDNS — always probe via Tailscale URL.
  gw="$(modelrouter_gateway_tailscale_url)"
  ssh -o ConnectTimeout=5 "$host" \
    "curl -sf --max-time 4 ${gw}/health/liveliness && echo '  ok  tower→mini gateway' || echo '  down tower→mini gateway'" || true
else
  echo "  skip gateway-tower  (ssh unreachable — set KC_TOWER_SSH)"
fi

exit "$fail"

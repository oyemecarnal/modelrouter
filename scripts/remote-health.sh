#!/usr/bin/env bash
# Ping ModelRouter health on laptop + kc-mini (+ optional tower SSH).
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

echo "==> Remote health"
fail=0

check_url "laptop" "http://127.0.0.1:${MODELROUTER_PORT:-3000}" || fail=1
check_url "kc-mini" "http://kc-mini-lan:${MODELROUTER_PORT:-3000}" || fail=1

TOWER_SSH="${KC_TOWER_SSH:-kc-tower-lan}"
if ssh -o ConnectTimeout=3 -o BatchMode=yes "$TOWER_SSH" 'true' 2>/dev/null; then
  echo "  ok  kc-tower  ssh $TOWER_SSH"
  ssh -o ConnectTimeout=5 "$TOWER_SSH" \
    "curl -sf --max-time 4 http://kc-mini-lan:${MODELROUTER_PORT:-3000}/health/liveliness && echo '  ok  tower→mini gateway' || echo '  down tower→mini gateway'" || true
else
  echo "  skip kc-tower  (ssh $TOWER_SSH unreachable — set KC_TOWER_SSH)"
fi

exit "$fail"

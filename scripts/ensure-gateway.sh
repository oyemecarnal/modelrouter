#!/usr/bin/env bash
# Start gateway if down — restart once, then suggest daemon-enable.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh" 2>/dev/null || true

ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; }

echo "==> Ensure laptop gateway"
echo ""

if MODELROUTER_ROOT="$ROOT" "$ROOT/scripts/healthcheck.sh" &>/dev/null; then
  ok "Gateway already up"
  if launchctl list 2>/dev/null | grep -q com.modelrouter; then
    ok "launchd job loaded (com.modelrouter)"
  else
    warn "launchd not loaded — run: make daemon-enable"
  fi
  exit 0
fi

warn "Gateway down — running make restart"
"$ROOT/scripts/stop.sh" 2>/dev/null || true
"$ROOT/scripts/start-daemon.sh"
sleep 2

if MODELROUTER_ROOT="$ROOT" "$ROOT/scripts/healthcheck.sh" &>/dev/null; then
  ok "Gateway up after restart"
  if launchctl list 2>/dev/null | grep -q com.modelrouter; then
    ok "launchd job loaded (com.modelrouter)"
  else
    warn "launchd not loaded — run: make daemon-enable (docs/LAPTOP_DAEMON.md)"
  fi
  exit 0
fi

fail "Gateway still down after restart"
echo ""
echo "Next:"
echo "  make daemon-enable   # auto-start at login — docs/LAPTOP_DAEMON.md"
echo "  make doctor-fix      # same as this script"
echo "  make doctor          # full diagnostic"
exit 1

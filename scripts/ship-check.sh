#!/usr/bin/env bash
# Pre-ship validation — test, lint, VERSION/CHANGELOG alignment, tower audit.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VER="$(cat VERSION 2>/dev/null || echo dev)"
ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; exit 1; }

echo "==> Ship check (v${VER})"
echo ""

echo "── Tests"
make test

echo ""
echo "── Lint"
make lint

echo ""
echo "── VERSION / CHANGELOG"
grep -q "\\[${VER}\\]" CHANGELOG.md || fail "CHANGELOG missing [${VER}] section"
ok "CHANGELOG has [${VER}]"

echo ""
echo "── Required scripts"
for s in connect-provider.sh strip-tower-llm-keys.sh ensure-gateway.sh oauth-start.sh; do
  test -x "$ROOT/scripts/$s" || fail "missing or not executable: scripts/$s"
done
ok "ship scripts executable"

echo ""
echo "── Tower audit (optional)"
if ./scripts/audit-tower-wires.sh; then
  ok "tower wires"
else
  warn "tower audit failed — fix before ship if kc-tower is online"
fi

echo ""
echo "── Gateway (optional)"
if ./scripts/healthcheck.sh &>/dev/null; then
  ok "laptop gateway up"
else
  warn "laptop gateway down — run: make ensure-gateway"
fi

echo ""
ok "ship-check passed — ready for /ship v${VER}"
echo "See docs/SHIP_CHECKLIST.md"

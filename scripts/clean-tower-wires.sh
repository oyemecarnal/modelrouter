#!/usr/bin/env bash
# Rewrite tower client.env and re-run wire audit (CLEAN_WIRES).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Clean tower wires"
echo "    1. push-client-env-tower (gateway auth only)"
echo "    2. audit-tower-wires"
echo ""

"$ROOT/scripts/push-client-env-to-tower.sh"
echo ""
exec "$ROOT/scripts/audit-tower-wires.sh"

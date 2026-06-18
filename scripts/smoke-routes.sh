#!/usr/bin/env bash
# Smoke primary alt-routed presets on kc-mini (fast + smart).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"

echo "==> Route smoke (kc-mini gateway)"
echo ""

"$ROOT/scripts/smoke-hermes-fast.sh"
echo ""
"$ROOT/scripts/smoke-hermes-smart.sh"
echo ""
echo "==> Route smoke passed"

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VER="$(cat "$ROOT/VERSION" 2>/dev/null || echo dev)"

echo "╔══════════════════════════════════════╗"
echo "║  ModelRouter homelab  v${VER}        ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "Gateway (LAN): http://kc-mini-lan:3000"
echo "Docs: docs/HOMELAB_GOALS.md"
echo ""

"$ROOT/scripts/doctor.sh" 2>/dev/null | sed -n '1,25p' || true
echo ""
"$ROOT/scripts/remote-health.sh" 2>/dev/null || true
echo ""
echo "── Cost review (header)"
"$ROOT/scripts/cost-review.sh" 2>/dev/null | sed -n '1,12p' || true

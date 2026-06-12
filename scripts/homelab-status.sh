#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VER="$(cat "$ROOT/VERSION" 2>/dev/null || echo dev)"
GW_URL="$(awk '/^gateway:/{f=1} f && /^  url:/{print $2; exit}' "$ROOT/config/hosts.yaml" 2>/dev/null || echo "http://Kevins-Mac-mini.local:3000")"

echo "╔══════════════════════════════════════╗"
echo "║  ModelRouter homelab  v${VER}        ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "Gateway (LAN): ${GW_URL}  (SSH: kc-mini-lan)"
echo "Docs: docs/HOMELAB_GOALS.md"
echo ""

"$ROOT/scripts/doctor.sh" 2>/dev/null | sed -n '1,25p' || true
echo ""
"$ROOT/scripts/remote-health.sh" 2>/dev/null || true
echo ""
echo "── Cost review (header)"
"$ROOT/scripts/cost-review.sh" 2>/dev/null | sed -n '1,12p' || true

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
echo ""
echo "── Usage rollup (24h)"
"$ROOT/scripts/usage-rollup.sh" --hours 24 2>/dev/null | sed -n '1,10p' || true
echo ""
echo "── Tower (kc-tower)"
TOWER_SSH="${KC_TOWER_SSH:-}"
if [[ -z "$TOWER_SSH" ]]; then
  for c in kc-tower kc-tower-lan; do
    ssh -o ConnectTimeout=3 -o BatchMode=yes "$c" 'true' 2>/dev/null && TOWER_SSH="$c" && break
  done
fi
if [[ -n "$TOWER_SSH" ]]; then
  echo "  SSH: $TOWER_SSH"
  ssh -o ConnectTimeout=4 "$TOWER_SSH" \
    'test -f ~/.config/modelrouter/client.env && echo "  client.env: ok" || echo "  client.env: missing — make push-client-env-tower"' 2>/dev/null \
    || echo "  client.env: check failed"
  echo "  wires: make audit-tower-wires  ·  make clean-tower-wires  ·  make guide-tower-strays"
else
  echo "  skip SSH — set KC_TOWER_SSH when tower is online"
  echo "  LAN path: make smoke-tower  (hermes-fast / cheap via Kevins-Mac-mini.local)"
fi
echo ""
echo "── Private API inventory"
echo "  make core-apis  →  data/CORE_APIS.md (gitignored, masked keys)"

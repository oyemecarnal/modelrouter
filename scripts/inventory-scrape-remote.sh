#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE="${MODELROUTER_REMOTE_HOST:-kc-mini-lan}"
REMOTE_DIR="${MODELROUTER_REMOTE_DIR:-/Users/kevinreed/dev/modelrouter}"

echo "==> Sync inventory harness → $REMOTE:$REMOTE_DIR"
rsync -avz "$ROOT/scripts/inventory-scrape.sh" "$ROOT/scripts/lib.sh" \
  "${REMOTE}:${REMOTE_DIR}/scripts/"
rsync -avz "$ROOT/modelrouter/machine_inventory.py" \
  "${REMOTE}:${REMOTE_DIR}/modelrouter/"
rsync -avz "$ROOT/config/inventory.yaml" \
  "${REMOTE}:${REMOTE_DIR}/config/"

echo "==> Remote inventory on $REMOTE"
ssh -o ConnectTimeout=8 "$REMOTE" "cd '$REMOTE_DIR' && chmod +x scripts/inventory-scrape.sh && ./scripts/inventory-scrape.sh" 2>&1

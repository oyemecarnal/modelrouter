#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env
REMOTE="$(modelrouter_remote_host)"
REMOTE_DIR="${MODELROUTER_REMOTE_DIR:-$HOME/dev/modelrouter}"

echo "==> Sync inventory harness → $REMOTE:$REMOTE_DIR"
rsync -avz "$ROOT/scripts/inventory-scrape.sh" "$ROOT/scripts/lib.sh" \
  "${REMOTE}:${REMOTE_DIR}/scripts/"
rsync -avz "$ROOT/modelrouter/machine_inventory.py" \
  "${REMOTE}:${REMOTE_DIR}/modelrouter/"
rsync -avz "$ROOT/config/inventory.yaml" \
  "${REMOTE}:${REMOTE_DIR}/config/"

echo "==> Remote inventory on $REMOTE"
ssh -o ConnectTimeout=8 "$REMOTE" "cd '$REMOTE_DIR' && chmod +x scripts/inventory-scrape.sh && ./scripts/inventory-scrape.sh" 2>&1

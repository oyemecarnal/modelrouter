#!/usr/bin/env bash
# Masked machine inventory — API keys + crypto surfaces in allowed paths only.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${MODELROUTER_INVENTORY_JSON:-$ROOT/data/inventory_snapshot.json}"
CONFIG="${MODELROUTER_INVENTORY_CONFIG:-$ROOT/config/inventory.yaml}"

# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_activate

PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -m modelrouter.machine_inventory \
  --config "$CONFIG" \
  --json "$OUT"

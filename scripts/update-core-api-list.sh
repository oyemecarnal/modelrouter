#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# Refresh inventory snapshot when stale (>7 days) for location hints
SNAP="$ROOT/data/inventory_snapshot.json"
if [[ ! -f "$SNAP" ]] || [[ "$(find "$SNAP" -mtime +7 2>/dev/null)" ]]; then
  PYTHONPATH="$ROOT" .venv/bin/python -m modelrouter.machine_inventory 2>/dev/null || true
fi
PYTHONPATH="$ROOT" .venv/bin/python -m modelrouter.core_api_list

#!/usr/bin/env bash
# Generic connector entry — dispatches to scripts/connect-{id}.sh per config/connectors.yaml
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REGISTRY="$ROOT/config/connectors.yaml"

usage() {
  echo "Usage: connect-provider.sh <id> [--no-push] [--no-restart]"
  echo ""
  PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
import yaml
from pathlib import Path
data = yaml.safe_load(Path('$REGISTRY').read_text()) or {}
for cid, c in sorted((data.get('connectors') or {}).items()):
    print(f'  {cid:12}  {c.get(\"label\", cid)}  ({c.get(\"env\", \"\")})')
" 2>/dev/null || echo "  groq | anthropic"
  echo ""
  echo "Docs: docs/POSITIONING.md · docs/CONNECTOR_SPEC.md"
}

[[ $# -ge 1 ]] || { usage; exit 1; }
ID="$1"
shift

SCRIPT="$ROOT/scripts/connect-${ID}.sh"
if [[ ! -x "$SCRIPT" ]]; then
  echo "Unknown or missing connector: $ID (no $SCRIPT)" >&2
  usage
  exit 1
fi

exec "$SCRIPT" "$@"

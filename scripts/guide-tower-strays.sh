#!/usr/bin/env bash
# Print tower cleanup commands for stray provider keys (no remote edits).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Tower stray-key guide (read-only)"
echo ""

if ! "$ROOT/scripts/audit-tower-wires.sh" 2>&1; then
  echo ""
  echo "── Suggested fixes (run on kc-tower as root/agent user)"
  echo "  1. source ~/.config/modelrouter/client.env   # gateway only"
  echo "  2. Edit ~/dev/coinbot/.env — remove OPENAI_API_KEY / GROQ_API_KEY / etc."
  echo "  3. From laptop: make clean-tower-wires && make audit-tower-wires"
  echo ""
  echo "Docs: docs/TOWER_CLEANUP.md"
  exit 1
fi

echo "Tower wires OK — no guide needed."

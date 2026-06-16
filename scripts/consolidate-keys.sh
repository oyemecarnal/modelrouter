#!/usr/bin/env bash
# Inventory-driven key consolidation report (read-only, masked).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Key consolidation report"
echo "    Goal: provider secrets on kc-mini modelrouter/.env only"
echo ""

if [[ -x ./scripts/inventory-scrape.sh ]]; then
  echo "── Local inventory (masked)"
  ./scripts/inventory-scrape.sh 2>/dev/null | grep -E '^  [A-Z_]+' | head -25 || true
fi

echo ""
echo "── Recommended actions"
echo "  1. make vault-scrape-collect  # network ingest → data/key_vault.json"
echo "  2. make vault-export-dry      # preview centralized .env merge"
echo "  3. make keys-sync-mini          # pull canonical .env from mini"
echo "  2. Remove OPENAI_API_KEY from ~/.zshrc (use 1Password / mini)"
echo "  3. Tower: config/client.env.example → gateway URL only"
echo "  4. make push-env-mini      # after rotate-master-key"
echo "  5. make inventory-mini     # verify mini is canonical"

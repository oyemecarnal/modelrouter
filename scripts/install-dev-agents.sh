#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENCY_SRC="${AGENCY_AGENTS_SRC:-}"
MODE="${1:-curated}"

# Default: pull from Mac mini
if [[ -z "$AGENCY_SRC" ]]; then
  if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new kc-mini-lan 'test -d ~/dev/agency_agents/agency-agents-main' 2>/dev/null; then
    AGENCY_SRC="kc-mini-lan:~/dev/agency_agents/agency-agents-main"
  elif [[ -d "$ROOT/.review/agency-agents-main" ]]; then
    AGENCY_SRC="$ROOT/.review/agency-agents-main"
  else
    echo "[agents] agency-agents not found. Set AGENCY_AGENTS_SRC or unzip on kc-mini." >&2
    exit 1
  fi
fi

CURATED=(
  engineering-sre
  engineering-devops-automator
  engineering-incident-response-commander
  engineering-backend-architect
  engineering-ai-engineer
  engineering-software-architect
)

sync_agent() {
  local category="$1" file="$2"
  local dest="$ROOT/agents/$(basename "$file")"
  if [[ "$AGENCY_SRC" == *:* ]]; then
    scp "${AGENCY_SRC%:*}:${AGENCY_SRC#*:}/${category}/${file}.md" "$dest"
  else
    cp "$AGENCY_SRC/${category}/${file}.md" "$dest"
  fi
  echo "[agents] → $dest"
}

mkdir -p "$ROOT/agents"

if [[ "$MODE" == "--all" ]]; then
  echo "[agents] Running upstream agency-agents installer for Cursor..."
  TMP=$(mktemp -d)
  if [[ "$AGENCY_SRC" == *:* ]]; then
    scp -r "${AGENCY_SRC%:*}:${AGENCY_SRC#*:}" "$TMP/agency-agents-main"
    AGENCY_SRC="$TMP/agency-agents-main"
  fi
  (cd "$AGENCY_SRC" && ./scripts/convert.sh --tool cursor 2>/dev/null || true)
  (cd "$ROOT" && "$AGENCY_SRC/scripts/install.sh" --tool cursor --no-interactive)
  echo "[agents] Installed full roster to .cursor/rules/"
  exit 0
fi

for slug in "${CURATED[@]}"; do
  sync_agent engineering "$slug"
done

if [[ "$AGENCY_SRC" == *:* ]]; then
  scp "${AGENCY_SRC%:*}:${AGENCY_SRC#*:}/specialized/specialized-mcp-builder.md" "$ROOT/agents/"
else
  cp "$AGENCY_SRC/specialized/specialized-mcp-builder.md" "$ROOT/agents/"
fi
echo "[agents] → $ROOT/agents/specialized-mcp-builder.md"

echo "[agents] Done. See agents/README.md for usage."

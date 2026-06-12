#!/usr/bin/env bash
# Launch widget with stdout/stderr captured for crash diagnosis.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SUPPORT="$HOME/Library/Application Support/TokenWidget"
VENV="$ROOT/.venv/bin/python3"
STAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

mkdir -p "$SUPPORT"

log_event() {
  printf '{"ts":"%s","event":"%s","pid":%s%s}\n' \
    "$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")" "$1" "$$" "${2:+,$2}" >> "$SUPPORT/widget_events.jsonl"
}

log_event "launcher_start"

{
  echo "===== $STAMP widget session start pid=$$ ====="
  cd "$ROOT"

  PANEL_FETCH="$(python3 -c "import json; from pathlib import Path; c={};
for p in [Path('$ROOT/config.json'), Path('$ROOT/config.local.json')]:
  c.update(json.loads(p.read_text())) if p.exists() else None
print('true' if c.get('widget_fetch_in_panel', False) else 'false')")"
  if [[ "$PANEL_FETCH" == "true" ]]; then
    "$VENV" scripts/fetch_usage.py
  fi

  "$VENV" widget/desktop_widget.py
  code=$?
  echo "===== $(date -u +"%Y-%m-%dT%H:%M:%SZ") widget exit code=$code pid=$$ ====="
  log_event "launcher_exit" "\"exit_code\":$code"
  exit "$code"
} >> "$SUPPORT/widget.stdout.log" 2>> "$SUPPORT/widget.stderr.log"

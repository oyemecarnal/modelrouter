#!/usr/bin/env bash
# Show widget process state and recent diagnostic events.
set -euo pipefail

SUPPORT="$HOME/Library/Application Support/TokenWidget"

echo "== Process =="
pgrep -fl "widget/desktop_widget.py|run_widget.sh|widget_watchdog" || echo "(not running)"

echo ""
echo "== Last 10 events =="
if [[ -f "$SUPPORT/widget_events.jsonl" ]]; then
  tail -10 "$SUPPORT/widget_events.jsonl"
else
  echo "(no events yet)"
fi

echo ""
echo "== widget.log (last 15 lines) =="
tail -15 "$SUPPORT/widget.log" 2>/dev/null || echo "(empty)"

echo ""
echo "== stderr (last 10 lines) =="
tail -10 "$SUPPORT/widget.stderr.log" 2>/dev/null || echo "(empty)"

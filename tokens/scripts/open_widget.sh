#!/usr/bin/env bash
# Open the widget in the user's GUI session (Terminal + pywebview window).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESKTOP="$HOME/Desktop/Token Widget.command"

pkill -f "widget/desktop_widget.py" 2>/dev/null || true
pkill -f "run_widget.sh" 2>/dev/null || true
sleep 0.5

open "$DESKTOP"

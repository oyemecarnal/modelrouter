#!/usr/bin/env bash
# Auto-restart widget after unexpected exit; logs restarts to widget_events.jsonl.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SUPPORT="$HOME/Library/Application Support/TokenWidget"
RUN="$ROOT/scripts/run_widget.sh"
MIN_UPTIME=15
RESTART_DELAY=3

mkdir -p "$SUPPORT"

log_event() {
  printf '{"ts":"%s","event":"%s","detail":"%s","pid":%s}\n' \
    "$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")" "$1" "$2" "$$" >> "$SUPPORT/widget_events.jsonl"
}

log_event "watchdog_start" "min_uptime=${MIN_UPTIME}s"

while true; do
  start=$(date +%s)
  log_event "watchdog_spawn" "starting run_widget.sh"
  bash "$RUN" || true
  code=$?
  end=$(date +%s)
  uptime=$((end - start))

  if [[ $uptime -lt $MIN_UPTIME ]]; then
    log_event "watchdog_crash_suspect" "exit=$code uptime=${uptime}s"
  else
    log_event "watchdog_normal_exit" "exit=$code uptime=${uptime}s"
  fi

  sleep "$RESTART_DELAY"
done

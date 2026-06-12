#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIDFILE="$ROOT/.pids/modelrouter.pid"
LOGFILE="${MODELROUTER_LOG:-$ROOT/data/modelrouter.log}"

mkdir -p "$ROOT/data" "$ROOT/.pids"

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "[modelrouter] Already running (PID $(cat "$PIDFILE"))"
  exit 0
fi

nohup "$ROOT/scripts/start.sh" >> "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"
echo "[modelrouter] Started daemon PID $(cat "$PIDFILE")"
echo "[modelrouter] Logs: $LOGFILE"

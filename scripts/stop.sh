#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIDFILE="$ROOT/.pids/modelrouter.pid"

if [[ ! -f "$PIDFILE" ]]; then
  echo "[modelrouter] Not running (no pidfile)"
  exit 0
fi

PID="$(cat "$PIDFILE")"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "[modelrouter] Stopped PID $PID"
else
  echo "[modelrouter] Stale pidfile — process not running"
fi
rm -f "$PIDFILE"

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env

PIDFILE="$ROOT/.pids/modelrouter.pid"
PORT="${MODELROUTER_PORT:-3000}"

stopped=false

if [[ -f "$PIDFILE" ]]; then
  PID="$(cat "$PIDFILE")"
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    echo "[modelrouter] Stopped PID $PID"
    stopped=true
  else
    echo "[modelrouter] Stale pidfile — process not running"
  fi
  rm -f "$PIDFILE"
elif ! lsof -ti :"$PORT" &>/dev/null; then
  echo "[modelrouter] Not running (no pidfile)"
  exit 0
fi

# Ensure nothing keeps listening after shell pipeline or crash orphans.
if lsof -ti :"$PORT" &>/dev/null; then
  lsof -ti :"$PORT" | xargs kill 2>/dev/null || true
  sleep 1
  if lsof -ti :"$PORT" &>/dev/null; then
    lsof -ti :"$PORT" | xargs kill -9 2>/dev/null || true
  fi
  echo "[modelrouter] Freed port $PORT"
  stopped=true
fi

if [[ "$stopped" == false ]]; then
  echo "[modelrouter] Not running"
fi

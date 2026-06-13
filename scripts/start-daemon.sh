#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env
PIDFILE="$ROOT/.pids/modelrouter.pid"
LOGFILE="${MODELROUTER_LOG:-$ROOT/data/modelrouter.log}"

mkdir -p "$ROOT/data" "$ROOT/.pids"

PORT="${MODELROUTER_PORT:-3000}"

if modelrouter_reconcile_pidfile && modelrouter_wait_healthy 5; then
  echo "[modelrouter] Already running (PID $(cat "$PIDFILE"))"
  exit 0
fi

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  if modelrouter_wait_healthy 15; then
    modelrouter_reconcile_pidfile || true
    echo "[modelrouter] Already running (PID $(cat "$PIDFILE"))"
    exit 0
  fi
  echo "[modelrouter] Stale process on pidfile — stopping"
  "$ROOT/scripts/stop.sh" || true
fi

lsof -ti :"${MODELROUTER_PORT:-3000}" 2>/dev/null | xargs kill -9 2>/dev/null || true

nohup "$ROOT/scripts/start.sh" >> "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"
echo "[modelrouter] Started daemon PID $(cat "$PIDFILE")"
echo "[modelrouter] Logs: $LOGFILE"

if modelrouter_wait_healthy 45; then
  modelrouter_reconcile_pidfile || true
  echo "[modelrouter] Health check passed"
else
  echo "[modelrouter] WARNING: not healthy after 45s — run: make doctor" >&2
  # Exit 0 for launchd KeepAlive — non-zero causes restart thrash
  exit 0
fi

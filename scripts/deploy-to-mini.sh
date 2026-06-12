#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_HOST="${MODELROUTER_REMOTE_HOST:-kc-mini-lan}"
REMOTE_DIR="${MODELROUTER_REMOTE_DIR:-/Users/kevinreed/dev/modelrouter}"

echo "[deploy] Syncing ModelRouter → ${REMOTE_HOST}:${REMOTE_DIR}"

rsync -avz --delete \
  --exclude '.venv' \
  --exclude '.review' \
  --exclude 'data/*.log' \
  --exclude '.pids' \
  --exclude '.DS_Store' \
  --exclude '.env' \
  "$ROOT/" "${REMOTE_HOST}:${REMOTE_DIR}/"

echo "[deploy] Installing on ${REMOTE_HOST}..."
ssh -o StrictHostKeyChecking=accept-new "$REMOTE_HOST" bash -s <<EOF
set -euo pipefail
cd "$REMOTE_DIR"
chmod +x scripts/*.sh
./scripts/install.sh
./scripts/stop.sh 2>/dev/null || true
./scripts/start-daemon.sh
sleep 3
./scripts/healthcheck.sh || echo "[deploy] Health check failed — check logs on mini"
EOF

echo "[deploy] Done. ModelRouter on ${REMOTE_HOST}:${REMOTE_DIR}"
echo "[deploy] Enable auto-start: ssh ${REMOTE_HOST} 'cd ${REMOTE_DIR} && make daemon-enable'"

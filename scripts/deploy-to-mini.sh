#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env
REMOTE_HOST="$(modelrouter_remote_host)"
REMOTE_DIR="${MODELROUTER_REMOTE_DIR:-$HOME/dev/modelrouter}"

echo "[deploy] Syncing ModelRouter → ${REMOTE_HOST}:${REMOTE_DIR}"

rsync -avz --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '.review' \
  --exclude '__pycache__' \
  --exclude 'data/' \
  --exclude '.pids' \
  --exclude '.DS_Store' \
  --exclude '.env' \
  --exclude 'tokens/.venv' \
  "$ROOT/" "${REMOTE_HOST}:${REMOTE_DIR}/"

echo "[deploy] Installing on ${REMOTE_HOST}..."
ssh -o StrictHostKeyChecking=accept-new "$REMOTE_HOST" bash -s <<EOF
set -euo pipefail
cd "$REMOTE_DIR"
chmod +x scripts/*.sh
./scripts/install.sh
./scripts/stop.sh 2>/dev/null || true
sleep 2
./scripts/stop.sh 2>/dev/null || true
MODELROUTER_WORKERS=1 ./scripts/start-daemon.sh
./scripts/issue-project-keys.sh 2>/dev/null || true
./scripts/healthcheck.sh || echo "[deploy] Health check failed — check logs on mini"
EOF

echo "[deploy] Done. ModelRouter on ${REMOTE_HOST}:${REMOTE_DIR}"
echo "[deploy] Enable auto-start: make daemon-enable-mini"

echo "[deploy] Remote health check..."
if "$ROOT/scripts/remote-health.sh"; then
  echo "[deploy] Remote health OK"
else
  echo "[deploy] WARNING: remote health check failed — run: make doctor" >&2
fi

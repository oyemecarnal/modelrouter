#!/usr/bin/env bash
# Enable ModelRouter launchd auto-start on kc-mini.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"

REMOTE_HOST="${MODELROUTER_REMOTE_HOST:-kc-mini-lan}"
REMOTE_DIR="${MODELROUTER_REMOTE_DIR:-$HOME/dev/modelrouter}"

echo "==> daemon-enable on ${REMOTE_HOST}"
ssh -o ConnectTimeout=8 "$REMOTE_HOST" bash -s <<EOF
set -euo pipefail
cd "$REMOTE_DIR"
if [[ ! -f Makefile ]]; then
  echo "[daemon-enable-mini] ${REMOTE_DIR} missing — run: make deploy-mini" >&2
  exit 1
fi
make daemon-enable
launchctl list 2>/dev/null | grep -E 'com\.modelrouter' || true
EOF
echo "[daemon-enable-mini] Done"

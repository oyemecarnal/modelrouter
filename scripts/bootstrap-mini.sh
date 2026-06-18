#!/usr/bin/env bash
# Deploy code to kc-mini, enable launchd, push alt keys when present.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"

SKIP_DEPLOY=0
for arg in "$@"; do
  case "$arg" in
    --skip-deploy) SKIP_DEPLOY=1 ;;
  esac
done

echo "==> Bootstrap kc-mini (deploy + daemon + alt keys)"

if [[ "$SKIP_DEPLOY" -eq 0 ]]; then
  "$ROOT/scripts/deploy-to-mini.sh"
else
  echo "[bootstrap-mini] --skip-deploy — skipping rsync"
fi

"$ROOT/scripts/daemon-enable-mini.sh"
"$ROOT/scripts/push-alt-keys-mini.sh" || true

REMOTE_HOST="$(modelrouter_remote_host)"
REMOTE_DIR="${MODELROUTER_REMOTE_DIR:-$HOME/dev/modelrouter}"
echo "[bootstrap-mini] Remote version:"
ssh -o ConnectTimeout=8 "$REMOTE_HOST" "cat ${REMOTE_DIR}/VERSION 2>/dev/null || echo unknown"
echo "[bootstrap-mini] Done — make smoke-hermes-smart when gateway is up"

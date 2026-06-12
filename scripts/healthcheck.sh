#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env

HOST="${MODELROUTER_HOST:-127.0.0.1}"
PORT="${MODELROUTER_PORT:-3000}"
KEY="${MODELROUTER_MASTER_KEY:-sk-modelrouter-local-dev}"
# When bound to 0.0.0.0, probe via loopback for local health checks.
CURL_HOST="${HOST}"
[[ "$CURL_HOST" == "0.0.0.0" || "$CURL_HOST" == "::" ]] && CURL_HOST="127.0.0.1"

health=$(curl -sf "http://${CURL_HOST}:${PORT}/health" 2>/dev/null || echo '{"status":"down"}')
echo "$health" | python3 -m json.tool 2>/dev/null || echo "$health"

if echo "$health" | grep -q '"healthy_instances"'; then
  echo "status: healthy"
  exit 0
fi

if curl -sf "http://${CURL_HOST}:${PORT}/health/liveliness" &>/dev/null; then
  echo "status: alive"
  exit 0
fi

if curl -sf "http://${CURL_HOST}:${PORT}/v1/models" \
  -H "Authorization: Bearer ${KEY}" &>/dev/null; then
  echo "status: models_ok"
  exit 0
fi

echo "status: down"
exit 1

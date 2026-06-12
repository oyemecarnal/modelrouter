#!/usr/bin/env bash
set -euo pipefail

HOST="${MODELROUTER_HOST:-127.0.0.1}"
PORT="${MODELROUTER_PORT:-3000}"
KEY="${MODELROUTER_MASTER_KEY:-sk-modelrouter-local-dev}"

health=$(curl -sf "http://${HOST}:${PORT}/health" 2>/dev/null || echo '{"status":"down"}')
echo "$health" | python3 -m json.tool 2>/dev/null || echo "$health"

if echo "$health" | grep -q '"healthy_instances"'; then
  exit 0
fi

# LiteLLM /health returns healthy_instances when up
if curl -sf "http://${HOST}:${PORT}/health/liveliness" &>/dev/null; then
  echo "status: alive"
  exit 0
fi

# Fallback: models endpoint
if curl -sf "http://${HOST}:${PORT}/v1/models" \
  -H "Authorization: Bearer ${KEY}" &>/dev/null; then
  echo "status: models_ok"
  exit 0
fi

echo "status: down"
exit 1

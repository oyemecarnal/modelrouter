#!/usr/bin/env bash
# Verify ModelRouter is reachable the way Cursor should use it (OpenAI-compatible /v1).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env

HOST="${MODELROUTER_HOST:-127.0.0.1}"
PORT="${MODELROUTER_PORT:-3000}"
KEY="${MODELROUTER_MASTER_KEY:-}"
CURL_HOST="${HOST}"
[[ "$CURL_HOST" == "0.0.0.0" || "$CURL_HOST" == "::" ]] && CURL_HOST="127.0.0.1"
BASE="http://${CURL_HOST}:${PORT}/v1"
LOG="${MODELROUTER_LOG:-$ROOT/data/modelrouter.log}"

ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; exit 1; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

echo "==> Cursor wiring smoke"
echo "    Base URL (set in Cursor): ${BASE}"
echo ""

if [[ -z "$KEY" || "$KEY" == *change-me* || "$KEY" == *local-dev* ]]; then
  fail "MODELROUTER_MASTER_KEY unset or placeholder — set in .env"
fi
ok "MODELROUTER_MASTER_KEY is set (${KEY:0:8}…)"

if ! curl -sf "${BASE}/models" -H "Authorization: Bearer ${KEY}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ids = [m['id'] for m in d.get('data', [])]
need = ['smart', 'fast', 'cheap', 'hermes-fast']
missing = [n for n in need if n not in ids]
if missing:
    raise SystemExit('missing: ' + ','.join(missing))
print('  ok models:', ', '.join(need))
" 2>/dev/null; then
  fail "/v1/models — is gateway running? (make restart)"
fi

MARKER="cursor-smoke-$(date +%s)"
BODY=$(cat <<EOF
{"model":"fast","messages":[{"role":"user","content":"Reply with exactly: ${MARKER}"}],"max_tokens":16}
EOF
)
RESP=$(curl -sf "${BASE}/chat/completions" \
  -H "Authorization: Bearer ${KEY}" \
  -H "Content-Type: application/json" \
  -d "$BODY" 2>/dev/null || true)

if [[ -z "$RESP" ]]; then
  fail "/v1/chat/completions failed"
fi

echo "$RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d.get('error'):
    raise SystemExit(d['error'].get('message', d['error']))
c = d['choices'][0]['message']['content']
print('  ok chat:', c[:60].replace(chr(10), ' '))
" || fail "chat completion parse error"

sleep 1
if [[ -f "$LOG" ]] && grep -qE 'request_success|"event": "request_success"' "$LOG" 2>/dev/null; then
  ok "Gateway log shows request_success ($LOG)"
elif [[ -f "$LOG" ]] && tail -30 "$LOG" | grep -q "LiteLLM completion" 2>/dev/null; then
  ok "Gateway log shows LiteLLM activity ($LOG)"
else
  warn "Structured JSON not in log file — callback may log to stdout; chat curl succeeded"
fi

echo ""
echo "── Cursor settings (human)"
echo "  OpenAI API Base URL: ${BASE}"
echo "  API Key:             MODELROUTER_MASTER_KEY from .env (crsr_* OK)"
echo "  Override OpenAI URL: ON — do not use api.openai.com"
echo ""
echo "  Docs: docs/CURSOR_WIRING.md"

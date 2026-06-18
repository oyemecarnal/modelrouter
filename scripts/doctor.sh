#!/usr/bin/env bash
# ModelRouter health + config diagnostic (no secret values printed).
# Full dashboard: make homelab-status
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

ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; }

echo "==> ModelRouter doctor"
echo "    Host: $(hostname -s 2>/dev/null || hostname)"
echo "    Root: $ROOT"
echo ""

echo "── Process"
LISTEN_PID="$(modelrouter_port_listener_pid)"
PIDFILE_PID=""
if [[ -f "$ROOT/.pids/modelrouter.pid" ]]; then
  PIDFILE_PID="$(cat "$ROOT/.pids/modelrouter.pid")"
fi
if [[ -n "$LISTEN_PID" ]]; then
  echo "$LISTEN_PID" > "$ROOT/.pids/modelrouter.pid"
  ok "Port $PORT listener (PID $LISTEN_PID)"
elif [[ -n "$PIDFILE_PID" ]] && kill -0 "$PIDFILE_PID" 2>/dev/null; then
  fail "Stale daemon PID $PIDFILE_PID — wrapper alive but nothing on :$PORT"
  echo "  fix: make doctor-fix"
elif [[ -n "$PIDFILE_PID" ]]; then
  fail "Stale pidfile (PID $PIDFILE_PID not running)"
else
  fail "Daemon not running"
fi

echo ""
echo "── Health"
GATEWAY_UP=0
if MODELROUTER_ROOT="$ROOT" "$ROOT/scripts/healthcheck.sh" &>/dev/null; then
  GATEWAY_UP=1
  ok "Healthcheck passed"
else
  fail "Healthcheck failed — gateway not responding"
  echo "  fix: make doctor-fix   (or make daemon-enable for login auto-start)"
fi

echo ""
echo "── Security"
if [[ -z "$KEY" || "$KEY" == *change-me* || "$KEY" == *local-dev* ]]; then
  warn "MODELROUTER_MASTER_KEY is placeholder — run: make rotate-master-key"
else
  ok "MODELROUTER_MASTER_KEY is set (custom)"
fi
if [[ "${LITELLM_SALT_KEY:-}" == "${MODELROUTER_MASTER_KEY:-}" ]]; then
  warn "LITELLM_SALT_KEY equals master key — use a distinct salt"
elif [[ -z "${LITELLM_SALT_KEY:-}" || "${LITELLM_SALT_KEY}" == *change-me* ]]; then
  warn "LITELLM_SALT_KEY is placeholder — required before Docker/Postgres deploy"
fi

echo ""
echo "── Provider keys in .env"
for k in OPENAI_API_KEY ANTHROPIC_API_KEY GOOGLE_API_KEY GROQ_API_KEY MISTRAL_API_KEY; do
  v="${!k:-}"
  if [[ -n "$v" ]]; then ok "$k set"
  else warn "$k empty"
  fi
done

if [[ "$GATEWAY_UP" -eq 1 ]]; then
  echo ""
  echo "── Policy presets"
  MODELS_JSON="$(curl -sf "http://${CURL_HOST}:${PORT}/v1/models" -H "Authorization: Bearer ${KEY}" 2>/dev/null || true)"
  if [[ -n "$MODELS_JSON" ]] && echo "$MODELS_JSON" | \
     python3 -c "import sys,json; d=json.load(sys.stdin); ids=[m['id'] for m in d.get('data',[])]; need=['hermes-fast','hermes-smart','cheap','code','offline']; missing=[n for n in need if n not in ids]; print('missing:'+','.join(missing) if missing else 'ok')" 2>/dev/null | grep -q ok; then
    ok "Presets registered on /v1/models"
  else
    warn "Policy presets not verified — run: make sync-gateway-config && make restart"
  fi
fi

echo ""
echo "── Dashboard"
echo "  make homelab-status     # paths, keys, remote health, usage header"
echo "  make doctor-fix         # restart gateway if down"
echo "  make keys-audit         # masked key inventory"
echo "  make connect-key PROVIDER=groq   # paste provider key"

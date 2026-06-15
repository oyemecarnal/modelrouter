#!/usr/bin/env bash
# ModelRouter health + config + keys diagnostic (no secret values printed).
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
LISTEN_PID="$(lsof -ti :"$PORT" 2>/dev/null | head -1 || true)"
if [[ -f "$ROOT/.pids/modelrouter.pid" ]] && kill -0 "$(cat "$ROOT/.pids/modelrouter.pid")" 2>/dev/null; then
  ok "Daemon PID $(cat "$ROOT/.pids/modelrouter.pid")"
elif [[ -n "$LISTEN_PID" ]]; then
  echo "$LISTEN_PID" > "$ROOT/.pids/modelrouter.pid"
  warn "Pidfile reconciled from port $PORT (PID $LISTEN_PID)"
else
  fail "Daemon not running (stale or missing pidfile)"
fi
if [[ -n "$LISTEN_PID" ]]; then
  ok "Port $PORT in use (PID $LISTEN_PID)"
else
  fail "Nothing listening on $PORT"
fi

echo ""
echo "── Health"
if MODELROUTER_ROOT="$ROOT" "$ROOT/scripts/healthcheck.sh" &>/dev/null; then
  ok "Healthcheck passed"
else
  fail "Healthcheck failed — run: make restart"
fi

echo ""
echo "── Security (human action if flagged)"
if [[ -z "$KEY" || "$KEY" == *change-me* || "$KEY" == *local-dev* ]]; then
  warn "MODELROUTER_MASTER_KEY is placeholder — run: make rotate-master-key (then update Cursor)"
else
  ok "MODELROUTER_MASTER_KEY is set (custom)"
fi
if [[ "${LITELLM_SALT_KEY:-}" == "${MODELROUTER_MASTER_KEY:-}" ]]; then
  warn "LITELLM_SALT_KEY equals master key — use a distinct salt for Docker/Postgres"
elif [[ -z "${LITELLM_SALT_KEY:-}" || "${LITELLM_SALT_KEY}" == *change-me* ]]; then
  warn "LITELLM_SALT_KEY is placeholder — required before Docker/Postgres deploy"
fi

echo ""
echo "── Provider keys in .env"
for k in OPENAI_API_KEY ANTHROPIC_API_KEY GOOGLE_API_KEY GROQ_API_KEY MISTRAL_API_KEY OPENROUTER_API_KEY; do
  v="${!k:-}"
  if [[ -n "$v" ]]; then ok "$k set"
  else warn "$k empty"
  fi
done
if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then
  warn "OPENROUTER_API_KEY set but OpenRouter is stubbed (not routed) — optional paid backup"
fi

echo ""
echo "── Policy presets"
MODELS_JSON="$(curl -sf "http://${CURL_HOST}:${PORT}/v1/models" -H "Authorization: Bearer ${KEY}" 2>/dev/null || true)"
if [[ -n "$MODELS_JSON" ]] && echo "$MODELS_JSON" | \
   python3 -c "import sys,json; d=json.load(sys.stdin); ids=[m['id'] for m in d.get('data',[])]; need=['hermes-fast','hermes-smart','cheap','code','offline']; missing=[n for n in need if n not in ids]; print('missing:'+','.join(missing) if missing else 'ok')" 2>/dev/null | grep -q ok; then
  ok "Presets registered (hermes-fast, hermes-smart, cheap, code, offline)"
else
  warn "Policy presets not verified (gateway down or missing from /v1/models)"
fi

echo ""
echo "── Route hints (widget loop)"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -m modelrouter.route_policy --project smalshi-hermes 2>/dev/null | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(d['preset']+': '+d['reason'])" && \
    ok "Route policy wrote data/route_hints.json"
else
  warn "venv missing — run make install"
fi

echo ""
echo "── Remote (kc-mini)"
if ssh -o ConnectTimeout=4 kc-mini-lan 'test -d ~/dev/modelrouter' 2>/dev/null; then
  ok "kc-mini-lan reachable, modelrouter dir exists"
  ssh -o ConnectTimeout=4 kc-mini-lan 'cd ~/dev/modelrouter && ./scripts/healthcheck.sh' 2>/dev/null | tail -1 || warn "mini healthcheck failed"
else
  warn "kc-mini-lan unreachable"
fi

echo ""
echo "── Next steps"
echo "  make restart              # if unhealthy"
echo "  make route-hints          # refresh widget → routing hints"
echo "  make push-client-env-tower  # when tower SSH is up"
echo "  make rotate-master-key    # if master key placeholder"
echo "  make deploy-mini          # sync this tree to kc-mini"
echo "  make core-apis            # refresh gitignored data/CORE_APIS.md (masked)"
echo "  make check-key-hygiene    # salt distinct, provider keys, Groq rotate reminder"
echo "  make usage-rollup         # log-based metering by model/preset (24h default)"
echo "  make homelab-status       # doctor + remote-health + cost + usage header"
echo "  make connect-groq         # paste Groq key → .env → push-env-mini (Phase 2)"
echo "  make connect-anthropic    # paste Anthropic key → mini (hermes-smart / review)"
echo "  make connect-provider PROVIDER=anthropic  # registry dispatch (config/connectors.yaml)"
echo "  make smoke-hermes-smart   # hermes-smart chat via mini gateway"

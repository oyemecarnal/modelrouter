#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "$ROOT/scripts/lib.sh"

PORT="${MODELROUTER_PORT:-3000}"
HOST="${MODELROUTER_HOST:-127.0.0.1}"
WORKERS="${MODELROUTER_WORKERS:-1}"
LOGFILE="${MODELROUTER_LOG:-$ROOT/data/modelrouter.log}"

mkdir -p "$ROOT/data" "$ROOT/.pids"

modelrouter_activate

# ── Secrets (1Password + .env) ───────────────────────────────────────
python3 "$ROOT/scripts/load_secrets.py"
set -a
# shellcheck disable=SC1091
[[ -f "$ROOT/.env" ]] && source "$ROOT/.env"
set +a
# LiteLLM load_dotenv() reads .env — blank DATABASE_URL triggers Prisma without a DB
[[ -z "${DATABASE_URL:-}" ]] && unset DATABASE_URL
[[ -z "${DIRECT_URL:-}" ]] && unset DIRECT_URL

# ── Pick config based on infrastructure ────────────────────────────────
CONFIG="$ROOT/config/modelrouter.minimal.yaml"

if command -v redis-cli &>/dev/null && \
   redis-cli -h "${REDIS_HOST:-127.0.0.1}" -p "${REDIS_PORT:-6379}" ping &>/dev/null; then
  CONFIG="$ROOT/config/modelrouter.yaml"
  echo "[modelrouter] Redis detected — using full config (cache + router)"
else
  echo "[modelrouter] Redis not available — using minimal config"
fi

if [[ -f "$ROOT/config/modelrouter.local.yaml" ]]; then
  CONFIG="$ROOT/config/modelrouter.local.yaml"
  echo "[modelrouter] Using local override: $CONFIG"
fi

# ── Start LiteLLM proxy ────────────────────────────────────────────────
echo "[modelrouter] Starting LiteLLM proxy on ${HOST}:${PORT}"
echo "[modelrouter] Config: $CONFIG"
echo "[modelrouter] Log: $LOGFILE"

exec litellm \
  --config "$CONFIG" \
  --host "$HOST" \
  --port "$PORT" \
  --num_workers "$WORKERS" \
  2>&1 | tee -a "$LOGFILE"

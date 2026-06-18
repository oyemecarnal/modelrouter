#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source "$ROOT/scripts/lib.sh"

echo "==> ModelRouter install"
VENV="$(modelrouter_venv)"
echo "==> Python venv: $VENV"
echo "==> Project root: $ROOT"

modelrouter_install_python_deps

# Config files
[[ -f .env ]] || cp .env.example .env
[[ -f secrets.yaml ]] || cp secrets.example.yaml secrets.yaml

chmod +x scripts/*.sh
mkdir -p data .pids
"$VENV/bin/python" scripts/sync_gateway_config.py

if "$VENV/bin/litellm" --version &>/dev/null; then
  echo "==> LiteLLM: $("$VENV/bin/litellm" --version 2>&1 | head -1)"
else
  echo "==> ERROR: litellm not installed" >&2
  exit 1
fi

# Optional: 1Password CLI
if command -v op &>/dev/null; then
  echo "==> 1Password CLI found: $(op --version)"
else
  echo "==> 1Password CLI not found. Install: brew install 1password-cli"
  echo "    Provider keys can still be set in .env"
fi

# Optional: Redis (brew)
if command -v redis-cli &>/dev/null; then
  echo "==> Redis found"
else
  echo "==> Redis not found. Install for caching/failover: brew install redis && brew services start redis"
fi

# Optional: Docker
if command -v docker &>/dev/null; then
  echo "==> Docker found — run 'docker compose up -d' for full production stack"
else
  echo "==> Docker not found — local mode uses minimal config (no Redis cache)"
fi

echo ""
echo "==> Done. Next steps:"
echo "    1. Edit .env and/or secrets.yaml with your API keys"
echo "    2. ./scripts/start-daemon.sh"
echo "    3. ./scripts/healthcheck.sh"

#!/usr/bin/env bash
# Install tower client.env — gateway auth only, no provider keys.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env

TOWER_SSH="${KC_TOWER_SSH:-}"
if [[ -z "$TOWER_SSH" ]]; then
  for candidate in gateway-tower kc-tower kc-tower-lan; do
    if ssh -o ConnectTimeout=4 -o BatchMode=yes "$candidate" 'true' 2>/dev/null; then
      TOWER_SSH="$candidate"
      break
    fi
  done
fi

if [[ -z "$TOWER_SSH" ]]; then
  echo "[push-client-env] ERROR: no tower SSH host reachable (set KC_TOWER_SSH)" >&2
  exit 1
fi

KEY="${MODELROUTER_KEY_HERMES:-${MODELROUTER_MASTER_KEY:-}}"
if [[ -z "$KEY" ]]; then
  echo "[push-client-env] ERROR: MODELROUTER_KEY_HERMES or MODELROUTER_MASTER_KEY required" >&2
  exit 1
fi

GW_URL="$(modelrouter_gateway_tailscale_url)"
GW_BASE="${GW_URL%/}/v1"

REMOTE_ENV='~/.config/modelrouter/client.env'
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

cat > "$TMP" <<EOF
# ModelRouter gateway client — synced from laptop ($(date -u +%Y-%m-%d))
# Tower uses Tailscale IP (mDNS does not resolve on Linux)
OPENAI_API_BASE=${GW_BASE}
OPENAI_BASE_URL=${GW_BASE}
OPENAI_API_KEY=${KEY}
MODELROUTER_PRESET_ROUTINE=hermes-fast
MODELROUTER_PRESET_COMPLEX=hermes-smart
EOF

echo "[push-client-env] Installing on ${TOWER_SSH}:${REMOTE_ENV}"
ssh "$TOWER_SSH" 'mkdir -p ~/.config/modelrouter'
scp "$TMP" "${TOWER_SSH}:/tmp/modelrouter-client.env"
ssh "$TOWER_SSH" 'mv /tmp/modelrouter-client.env ~/.config/modelrouter/client.env && chmod 600 ~/.config/modelrouter/client.env'
echo "[push-client-env] Done. Tower agents: source ~/.config/modelrouter/client.env"

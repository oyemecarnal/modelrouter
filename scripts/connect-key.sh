#!/usr/bin/env bash
# Unified paste-key connector — all providers in config/connectors.yaml
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_activate

exec "$ROOT/.venv/bin/python" -m modelrouter.connect_key "$@"

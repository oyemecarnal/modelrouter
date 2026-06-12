#!/usr/bin/env bash
# Fail closed when MODELROUTER_MASTER_KEY is a known placeholder (LAN safety).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env

mk="${MODELROUTER_MASTER_KEY:-}"
allow="${MODELROUTER_ALLOW_PLACEHOLDER:-}"

if [[ "$allow" == "1" ]]; then
  exit 0
fi

if [[ -z "$mk" ]] || [[ "$mk" == *change-me* ]] || [[ "$mk" == "sk-modelrouter-local-dev" ]]; then
  echo "[modelrouter] REFUSED: MODELROUTER_MASTER_KEY is missing or placeholder." >&2
  echo "[modelrouter] Run: make rotate-master-key" >&2
  echo "[modelrouter] Dev only: MODELROUTER_ALLOW_PLACEHOLDER=1 make start" >&2
  exit 1
fi

if [[ ${#mk} -lt 24 ]]; then
  echo "[modelrouter] REFUSED: MODELROUTER_MASTER_KEY too short (${#mk} chars)." >&2
  exit 1
fi

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
# shellcheck disable=SC1091
[[ -f "$ENV_FILE" ]] && source "$ROOT/scripts/lib.sh" && modelrouter_load_env

PYTHONPATH="$ROOT" python3 <<PY
from pathlib import Path
import os

path = Path("$ENV_FILE")
master = os.environ.get("MODELROUTER_MASTER_KEY", "")
if not master:
    raise SystemExit("Set MODELROUTER_MASTER_KEY in .env first")

keys = {
    "MODELROUTER_KEY_HERMES": "smalshi-hermes",
    "MODELROUTER_KEY_KALSHI": "kalshi-bot",
    "MODELROUTER_KEY_COINBOT": "coinbot",
    "MODELROUTER_KEY_CURSOR": "cursor-dev",
    "MODELROUTER_KEY_AGENTS": "modelrouter-agents",
}
lines = path.read_text().splitlines() if path.exists() else []
existing = {l.split("=", 1)[0].strip() for l in lines if "=" in l and not l.strip().startswith("#")}
out = list(lines)
for var, project in keys.items():
    if var in existing:
        continue
    out.append(f"# Project virtual key ({project}) — native mode uses master until Docker+DB")
    out.append(f"{var}={master}")
path.write_text("\n".join(out) + "\n")
print(f"[project-keys] Ensured project key vars in {path}")
PY

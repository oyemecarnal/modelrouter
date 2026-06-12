#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
REFRESH=false
for arg in "$@"; do
  [[ "$arg" == "--refresh" ]] && REFRESH=true
done

# shellcheck disable=SC1091
[[ -f "$ENV_FILE" ]] && source "$ROOT/scripts/lib.sh" && modelrouter_load_env

REFRESH="$REFRESH" PYTHONPATH="$ROOT" python3 <<PY
from pathlib import Path
import os

path = Path("$ENV_FILE")
master = os.environ.get("MODELROUTER_MASTER_KEY", "")
refresh = os.environ.get("REFRESH", "false").lower() == "true"
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
out = []
seen = set()
for line in lines:
    if "=" in line and not line.strip().startswith("#"):
        k = line.split("=", 1)[0].strip()
        if k in keys and (refresh or k not in seen):
            if k not in seen:
                out.append(f"# Project virtual key ({keys[k]}) — native mode uses master until Docker+DB")
            out.append(f"{k}={master}")
            seen.add(k)
            continue
        seen.add(k)
    out.append(line)
for var, project in keys.items():
    if var not in seen:
        out.append(f"# Project virtual key ({project}) — native mode uses master until Docker+DB")
        out.append(f"{var}={master}")
path.write_text("\n".join(out).rstrip() + "\n")
action = "Refreshed" if refresh else "Ensured"
print(f"[project-keys] {action} project key vars in {path}")
PY

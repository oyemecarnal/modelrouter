#!/usr/bin/env bash
# Generate a new MODELROUTER_MASTER_KEY (and distinct LITELLM_SALT_KEY) in .env.
# HUMAN: update Cursor / Continue / agents with the new key after running this.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"

new_key() { openssl rand -hex 24 | sed 's/^/sk-mr-/'; }

MASTER="$(new_key)"
SALT="$(new_key)"

python3 - "$ENV_FILE" "$MASTER" "$SALT" <<'PY'
import sys
from pathlib import Path
path, master, salt = sys.argv[1:4]
lines = Path(path).read_text().splitlines() if Path(path).exists() else []
out = {}
for line in lines:
    if not line.strip() or line.strip().startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    out[k.strip()] = v
out["MODELROUTER_MASTER_KEY"] = master
out["LITELLM_SALT_KEY"] = salt
ordered = []
seen = set()
for line in lines:
    if "=" in line and not line.strip().startswith("#"):
        k = line.split("=", 1)[0].strip()
        if k in out and k not in seen:
            ordered.append(f"{k}={out[k]}")
            seen.add(k)
        elif k not in seen:
            ordered.append(line)
            seen.add(k)
    else:
        ordered.append(line)
for k in ("MODELROUTER_MASTER_KEY", "LITELLM_SALT_KEY"):
    if k not in seen:
        ordered.append(f"{k}={out[k]}")
Path(path).write_text("\n".join(ordered) + "\n")
PY

echo "[rotate-master-key] Updated $ENV_FILE"
echo "[rotate-master-key] HUMAN ACTION REQUIRED:"
echo "  1. Cursor → Settings → Models → API key = new MODELROUTER_MASTER_KEY"
echo "  2. Base URL stays http://127.0.0.1:3000 (or kc-mini-lan:3000)"
echo "  3. make push-env-mini  # sync to mini if needed"
echo "  4. make restart"
mask="${MASTER:0:10}…${MASTER: -4}"
echo "  New key (masked): $mask"

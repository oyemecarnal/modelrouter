#!/usr/bin/env bash
# Rotate LITELLM_SALT_KEY only — does not change MODELROUTER_MASTER_KEY (Cursor stays working).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"

SALT="$(openssl rand -hex 24 | sed 's/^/sk-mr-salt-/')"

python3 - "$ENV_FILE" "$SALT" <<'PY'
import sys
from pathlib import Path
path, salt = sys.argv[1:3]
lines = Path(path).read_text().splitlines() if Path(path).exists() else []
out, seen = [], set()
for line in lines:
    if line.startswith("LITELLM_SALT_KEY="):
        out.append(f"LITELLM_SALT_KEY={salt}")
        seen.add("LITELLM_SALT_KEY")
    else:
        out.append(line)
if "LITELLM_SALT_KEY" not in seen:
    out.append(f"LITELLM_SALT_KEY={salt}")
Path(path).write_text("\n".join(out).rstrip() + "\n")
PY

echo "[rotate-salt-key] Updated LITELLM_SALT_KEY in $ENV_FILE (master key unchanged)"
mask="${SALT:0:14}…${SALT: -4}"
echo "[rotate-salt-key] New salt (masked): $mask"

#!/usr/bin/env bash
# Sync selected keys from local .env to kc-mini modelrouter .env (never prints values).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_HOST="${MODELROUTER_REMOTE_HOST:-kc-mini-lan}"
REMOTE_DIR="${MODELROUTER_REMOTE_DIR:-$HOME/dev/modelrouter}"
KEY_LIST="${*:-MISTRAL_API_KEY GROQ_API_KEY}"

python3 - "$ROOT/.env" "$KEY_LIST" <<'PY' > /tmp/modelrouter-keys.env
import sys
from pathlib import Path
want = set(sys.argv[2].split())
for line in Path(sys.argv[1]).read_text().splitlines():
    if "=" not in line or line.startswith("#"):
        continue
    k, v = line.split("=", 1)
    if k in want and v.strip():
        print(f"{k}={v.strip()}")
PY

echo "[push-env] Updating keys on ${REMOTE_HOST}..."
scp /tmp/modelrouter-keys.env "${REMOTE_HOST}:/tmp/modelrouter-keys.env"
ssh "$REMOTE_HOST" python3 - "$REMOTE_DIR/.env" <<'PY'
import sys
from pathlib import Path
updates = {}
for line in Path("/tmp/modelrouter-keys.env").read_text().splitlines():
    k, v = line.split("=", 1)
    updates[k] = v
path = Path(sys.argv[1])
lines = path.read_text().splitlines() if path.exists() else []
out, seen = [], set()
for line in lines:
    if "=" in line and not line.startswith("#"):
        k = line.split("=", 1)[0]
        if k in updates:
            out.append(f"{k}={updates[k]}")
            seen.add(k)
            continue
    out.append(line)
for k, v in updates.items():
    if k not in seen:
        out.append(f"{k}={v}")
path.write_text("\n".join(out) + "\n")
PY
rm -f /tmp/modelrouter-keys.env
ssh "$REMOTE_HOST" 'rm -f /tmp/modelrouter-keys.env'
echo "[push-env] Done."

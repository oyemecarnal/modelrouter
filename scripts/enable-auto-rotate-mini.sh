#!/usr/bin/env bash
# Enable 429 auto-rotate + restart on kc-mini (not PUSH — mini is canonical gateway).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"

REMOTE_HOST="${MODELROUTER_REMOTE_HOST:-kc-mini-lan}"
REMOTE_DIR="${MODELROUTER_REMOTE_DIR:-$HOME/dev/modelrouter}"
ENABLE=0
for arg in "$@"; do
  case "$arg" in
    --enable) ENABLE=1 ;;
  esac
done

GATES=(MODELROUTER_AUTO_VAULT_ROTATE MODELROUTER_AUTO_VAULT_RESTART)

ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

echo "==> Auto-rotate on ${REMOTE_HOST} (rotate + restart only)"
echo ""

STATUS="$(ssh -o ConnectTimeout=8 "$REMOTE_HOST" python3 - "$REMOTE_DIR/.env" "${GATES[@]}" <<'PY'
import sys
from pathlib import Path
path = Path(sys.argv[1])
gates = sys.argv[2:]
vals = {}
if path.exists():
    for line in path.read_text().splitlines():
        if "=" not in line or line.strip().startswith("#"):
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip()
for g in gates:
    print(f"{g}={vals.get(g, '')}")
push = vals.get("MODELROUTER_AUTO_VAULT_PUSH", "")
if push:
    print(f"MODELROUTER_AUTO_VAULT_PUSH={push}")
PY
)"

while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  key="${line%%=*}"
  val="${line#*=}"
  if [[ "$val" == "1" ]]; then
    ok "${key}=1"
  else
    warn "${key} unset"
  fi
done <<< "$STATUS"

if echo "$STATUS" | grep -q '^MODELROUTER_AUTO_VAULT_PUSH=1'; then
  warn "MODELROUTER_AUTO_VAULT_PUSH=1 on mini — should stay off (mini is push target, not source)"
fi

if [[ "$ENABLE" -eq 0 ]]; then
  echo ""
  echo "  Dry-run — pass --enable to set on mini, then: ssh ${REMOTE_HOST} 'cd ${REMOTE_DIR} && make restart'"
  exit 0
fi

echo ""
echo "── Enabling on mini .env"
ssh -o ConnectTimeout=8 "$REMOTE_HOST" python3 - "$REMOTE_DIR/.env" "${GATES[@]}" <<'PY'
import sys
from pathlib import Path
path = Path(sys.argv[1])
updates = {g: "1" for g in sys.argv[2:]}
lines = path.read_text().splitlines() if path.exists() else []
out, seen = [], set()
for line in lines:
    if "=" in line and not line.strip().startswith("#"):
        k = line.split("=", 1)[0].strip()
        if k in updates:
            out.append(f"{k}={updates[k]}")
            seen.add(k)
            continue
    out.append(line)
for k, v in updates.items():
    if k not in seen:
        out.append(f"{k}={v}")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("\n".join(out) + "\n")
print("ok")
PY

ok "auto-rotate gates written on mini"
echo "  Restart: ssh ${REMOTE_HOST} 'cd ${REMOTE_DIR} && make restart'"

#!/usr/bin/env bash
# Remove duplicate KEY= lines from .env (keeps last occurrence; never prints values).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${MODELROUTER_ENV:-$ROOT/.env}"
APPLY=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
  esac
done

[[ -f "$ENV_FILE" ]] || { echo "[dedupe-env] missing: $ENV_FILE" >&2; exit 1; }

PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" - "$ENV_FILE" "$APPLY" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
apply = sys.argv[2] == "1"
lines = path.read_text().splitlines()

out_rev: list[str] = []
seen: set[str] = set()
dupes: list[str] = []

for line in reversed(lines):
    s = line.strip()
    if s and not s.startswith("#") and "=" in line:
        key = line.split("=", 1)[0].strip()
        if key in seen:
            dupes.append(key)
            continue
        seen.add(key)
    out_rev.append(line)

out = list(reversed(out_rev))
print(f"[dedupe-env] {path.name}: {len(dupes)} duplicate key line(s) dropped")
if dupes:
    for k in sorted(set(dupes)):
        print(f"  - {k}")
if apply and dupes:
    path.write_text("\n".join(out) + "\n")
    print("[dedupe-env] applied")
elif dupes and not apply:
    print("[dedupe-env] dry-run — pass --apply to write")
PY

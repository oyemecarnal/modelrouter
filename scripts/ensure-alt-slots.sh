#!/usr/bin/env bash
# Ensure empty __ALT_1 lines exist for alt-routed providers (never prints values).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${MODELROUTER_ENV:-$ROOT/.env}"

[[ -f "$ENV_FILE" ]] || { echo "[ensure-alt-slots] missing: $ENV_FILE" >&2; exit 1; }

PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" - "$ENV_FILE" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
pairs = [
    ("OPENAI_API_KEY", "OPENAI_API_KEY__ALT_1"),
    ("ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY__ALT_1"),
    ("MISTRAL_API_KEY", "MISTRAL_API_KEY__ALT_1"),
    ("GROQ_API_KEY", "GROQ_API_KEY__ALT_1"),
]
existing = set()
for line in path.read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        existing.add(line.split("=", 1)[0].strip())

lines = path.read_text().splitlines()
added = []
for primary, alt in pairs:
    if alt in existing:
        continue
    out, inserted = [], False
    for line in lines:
        out.append(line)
        if not inserted and line.startswith(primary + "=") and not line.startswith(primary + "__"):
            out.append(alt + "=")
            inserted = True
            added.append(alt)
    if inserted:
        lines = out
    elif alt not in existing:
        lines.append(alt + "=")
        added.append(alt)

if added:
    path.write_text("\n".join(lines) + "\n")
    print("[ensure-alt-slots] added:", ", ".join(added))
else:
    print("[ensure-alt-slots] all __ALT_1 slots present")
PY

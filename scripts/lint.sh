#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
fail=0

echo "==> lint"

echo "── shell scripts"
if command -v shellcheck &>/dev/null; then
  while IFS= read -r -d '' f; do
    shellcheck -x "$f" || fail=1
  done < <(find scripts -name '*.sh' -print0)
else
  echo "  skip shellcheck (brew install shellcheck)"
  for f in scripts/*.sh; do bash -n "$f" || fail=1; done
fi

echo "── python"
PYTHONPATH="$ROOT" .venv/bin/python -m compileall -q modelrouter scripts/load_secrets.py 2>/dev/null || fail=1

echo "── yaml"
.venv/bin/python -c "
import yaml
from pathlib import Path
for p in Path('config').rglob('*.yaml'):
    yaml.safe_load(p.read_text())
    print(f'  ok {p}')
" || fail=1

if [[ $fail -eq 0 ]]; then
  echo "==> lint passed"
else
  echo "==> lint failed" >&2
  exit 1
fi

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> ModelRouter test ($(cat VERSION 2>/dev/null || echo dev))"

echo "── YAML"
.venv/bin/python -c "
import yaml
from pathlib import Path
for p in ['config/modelrouter.minimal.yaml', 'config/projects.yaml', 'config/hosts.yaml']:
    if Path(p).exists():
        yaml.safe_load(Path(p).read_text())
        print(f'  ok {p}')
"

echo "── Route policy"
PYTHONPATH="$ROOT" .venv/bin/python -m modelrouter.route_policy --project smalshi-hermes >/dev/null

echo "── Health (optional)"
if ./scripts/healthcheck.sh &>/dev/null; then
  echo "  ok gateway"
else
  echo "  skip gateway (down — run make restart)"
fi

echo "==> test passed"

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
PYTHONPATH="$ROOT" .venv/bin/python -m modelrouter.route_policy --all >/dev/null

echo "── Policy presets SSOT"
.venv/bin/python scripts/check_presets.py

echo "── Models catalog SSOT"
.venv/bin/python scripts/check_catalog.py

echo "── Preset max_tokens sync"
.venv/bin/python scripts/sync_preset_max_tokens.py | grep -qE 'in sync|Updated'

echo "── Preset catalog (widget snapshot)"
PYTHONPATH="$ROOT/tokens/scripts" .venv/bin/python -c "
from preset_catalog import load_preset_catalog
d = load_preset_catalog({'modelrouter_root': '$ROOT'})
assert len(d.get('presets', [])) >= 6, d
assert 'catalog_version' in d
print(f'  ok {len(d[\"presets\"])} policy presets')
"

echo "── Security (gitignore)"
.venv/bin/python -c "
from pathlib import Path
gi = Path('.gitignore').read_text()
assert 'data/CORE_APIS.md' in gi, 'CORE_APIS.md must stay gitignored'
print('  ok data/CORE_APIS.md gitignored')
"

echo "── Health (optional)"
if ./scripts/healthcheck.sh &>/dev/null; then
  echo "  ok gateway"
else
  echo "  skip gateway (down — run make restart)"
fi

echo "==> test passed"

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
print('  ok', len(d.get('presets', [])), 'policy presets')
"

echo "── Console grid"
PYTHONPATH="$ROOT/tokens/scripts" .venv/bin/python -c "
from console_grid import load_console_grid
d = load_console_grid({'modelrouter_root': '$ROOT'})
assert len(d.get('presets', [])) >= 6
assert len(d.get('models', [])) >= 5
print('  ok console:', len(d.get('presets', [])), 'presets,', len(d.get('models', [])), 'models')
"

echo "── Security (gitignore)"
.venv/bin/python -c "
from pathlib import Path
gi = Path('.gitignore').read_text()
assert 'data/CORE_APIS.md' in gi, 'CORE_APIS.md must stay gitignored'
print('  ok data/CORE_APIS.md gitignored')
"

echo "── Security (snapshot exports)"
PYTHONPATH="$ROOT/tokens/scripts" .venv/bin/python -c "
import json, re
from preset_catalog import load_preset_catalog
from console_grid import load_console_grid
SECRET_RE = re.compile(r'(?:sk-[A-Za-z0-9]{8,}|gsk_[A-Za-z0-9]{8,}|ant-api[A-Za-z0-9_-]{8,}|crsr_[A-Za-z0-9]{8,})')
cfg = {'modelrouter_root': '$ROOT'}
for name, data in [('policyPresets', load_preset_catalog(cfg)), ('consoleGrid', load_console_grid(cfg))]:
    blob = json.dumps(data)
    m = SECRET_RE.search(blob)
    assert not m, f'{name} snapshot may leak secrets ({m.group(0)[:12]}...)'
print('  ok snapshot exports (no raw key prefixes)')
"

echo "── Health (optional)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh" 2>/dev/null || true
modelrouter_reconcile_pidfile 2>/dev/null || true
if ./scripts/healthcheck.sh &>/dev/null; then
  echo "  ok gateway"
else
  echo "  skip gateway (down — run make restart)"
fi

echo "==> test passed"

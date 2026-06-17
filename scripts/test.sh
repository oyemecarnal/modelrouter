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

echo "── Wire exceptions config"
PYTHONPATH="$ROOT" .venv/bin/python -c "
import yaml
from pathlib import Path
p = Path('$ROOT/config/wire_exceptions.yaml')
data = yaml.safe_load(p.read_text()) or {}
assert 'exceptions' in data, 'wire_exceptions.yaml needs exceptions list'
for ex in data.get('exceptions') or []:
    assert ex.get('path_suffix') and ex.get('vars'), ex
print('  ok wire_exceptions.yaml', len(data.get('exceptions') or []), 'entries')
"

echo "── Connector validation"
PYTHONPATH="$ROOT" .venv/bin/python -c "
from modelrouter.env_store import validate_provider_key
assert validate_provider_key('GROQ_API_KEY', 'gsk_' + 'a' * 48) is None
assert validate_provider_key('GROQ_API_KEY', 'bad') is not None
assert validate_provider_key('ANTHROPIC_API_KEY', 'sk-ant-api03-' + 'x' * 40) is None
assert validate_provider_key('ANTHROPIC_API_KEY', 'sk-bad') is not None
assert validate_provider_key('OPENAI_API_KEY', 'sk-proj-' + 'x' * 40) is None
assert validate_provider_key('OPENAI_API_KEY', 'bad') is not None
assert validate_provider_key('MISTRAL_API_KEY', 'a' * 32) is None
assert validate_provider_key('MISTRAL_API_KEY', 'short') is not None
assert validate_provider_key('GOOGLE_API_KEY', 'AIza' + 'x' * 35) is None
assert validate_provider_key('GOOGLE_API_KEY', 'bad') is not None
assert validate_provider_key('DEEPSEEK_API_KEY', 'sk-' + 'x' * 40) is None
assert validate_provider_key('TOGETHER_API_KEY', 'a' * 32) is None
assert validate_provider_key('FIREWORKS_API_KEY', 'fw_' + 'x' * 40) is None
assert validate_provider_key('COHERE_API_KEY', 'b' * 32) is None
print('  ok env_store key validation (9 provider patterns)')
"

echo "── Connector registry"
test -x "$ROOT/scripts/connect-provider.sh" || { echo "  FAIL missing connect-provider.sh" >&2; exit 1; }
PYTHONPATH="$ROOT" .venv/bin/python -c "
import re
import yaml
from pathlib import Path

root = Path('$ROOT')
reg = yaml.safe_load((root / 'config/connectors.yaml').read_text()) or {}
connectors = reg.get('connectors') or {}
assert connectors, 'connectors.yaml empty'
secret_re = re.compile(r'(gsk_|sk-ant-|sk-[A-Za-z0-9]{10,})')
required = {'env', 'validate', 'script', 'make_target'}
for cid, c in connectors.items():
    missing = required - set(c or {})
    assert not missing, f'{cid} missing {missing}'
    blob = yaml.dump({cid: c})
    assert not secret_re.search(blob), f'{cid} registry may contain secret-like value'
    script = root / 'scripts' / c['script']
    assert script.is_file(), f'{cid} script missing: {script}'
    assert (root / 'scripts' / f\"connect-{cid}.sh\").is_file(), f'connect-{cid}.sh missing'
print('  ok connectors.yaml', len(connectors), 'entries + connect-provider')
"

echo "── Homelab status (widget)"
PYTHONPATH="$ROOT/tokens/scripts" .venv/bin/python -c "
from homelab_status import load_homelab_status
d = load_homelab_status({'modelrouter_root': '$ROOT', 'receiver': {'enabled': True, 'default_preset': 'classic-rg'}})
assert d.get('enabled') and len(d.get('leds', [])) >= 10, d
assert len(d.get('themePresets', {})) >= 5, d
assert len(d.get('rows', [])) >= 3, d
api_row = next((r for r in d['rows'] if r.get('id') == 'connectors'), {})
assert len(api_row.get('leds', [])) >= 4, 'registry-driven API KEY LEDs'
signup = [l for l in api_row.get('leds', []) if l.get('signup')]
assert len(signup) >= 5, 'connector signup URLs from registry'
assert len(d.get('registryConnectors', [])) >= 6, 'registryConnectors for widget menu'
rc = d['registryConnectors'][0]
assert rc.get('env'), 'registryConnectors need env for paste modal'
assert 'hints' in d, 'homelab_status should expose hints list'
print('  ok homelab_status', len(d['leds']), 'LEDs,', len(d['themePresets']), 'presets, hints=', len(d.get('hints', [])))
"

echo "── Connector paste (widget)"
PYTHONPATH="$ROOT/tokens/scripts:$ROOT" .venv/bin/python -c "
from connector_paste import _load_connector
from pathlib import Path
root = Path('$ROOT')
c = _load_connector(root, 'groq')
assert c['env'] == 'GROQ_API_KEY', c
print('  ok connector_paste registry lookup')
"

echo "── Tower scripts"
test -x "$ROOT/scripts/strip-tower-llm-keys.sh" || { echo "  FAIL strip-tower-llm-keys.sh not executable" >&2; exit 1; }
test -x "$ROOT/scripts/ensure-gateway.sh" || { echo "  FAIL ensure-gateway.sh" >&2; exit 1; }
test -x "$ROOT/scripts/ship-check.sh" || { echo "  FAIL ship-check.sh" >&2; exit 1; }
test -x "$ROOT/scripts/oauth-start.sh" || { echo "  FAIL oauth-start.sh" >&2; exit 1; }
echo "  ok tower + ship scripts"

echo "── OAuth stub"
oauth_out="$("$ROOT/scripts/oauth-start.sh" google 2>&1 || true)"
echo "$oauth_out" | grep -q "connect-google" || { echo "  FAIL oauth-start hint" >&2; exit 1; }
echo "  ok oauth-start stub"

echo "── Equity config"
PYTHONPATH="$ROOT/tokens/scripts" .venv/bin/python -c "
from fetch_equity import _broker_route, _default_cfg, _provider_for
from equity_remote_runner import _looks_encrypted
base = _default_cfg()
base['broker_routes'] = {
    'kraken': {'host': 'local', 'remote': False, 'instance_id': 'paper_kraken'},
    'coinbase': {'host': 'kc-mini-lan', 'remote': True},
    'kalshi': {'provider': 'kalshi'},
}
k = _broker_route('kraken', base)
assert k['host'] == 'local' and k.get('instance_id') == 'paper_kraken'
assert _provider_for('kalshi', base) == 'kalshi'
assert not _looks_encrypted('F8D/1+z5rV0kBPipp56cFT5cHbPkVS' + 'x'*40)
assert _looks_encrypted('gAAAAABpejRA6hEpOAuD')
print('  ok fetch_equity broker_routes + encrypted detect')
"

echo "── Price oracle"
PYTHONPATH="$ROOT/tokens/scripts" .venv/bin/python -c "
from price_oracle import spot_usd
p = spot_usd('BTC')
assert p is None or p > 0
print('  ok price_oracle')
"

echo "── Key vault"
PYTHONPATH="$ROOT" .venv/bin/python -c "
from modelrouter.key_vault import load_vault_config, merge_entries
cfg = load_vault_config()
assert cfg.get('permissions', {}).get('deny_vars')
merged = merge_entries({'keys': []}, [], cfg)
assert 'keys' in merged
print('  ok key_vault config + merge')
"

echo "── Key vault (masked exports)"
PYTHONPATH="$ROOT" .venv/bin/python -c "
from modelrouter.key_vault import list_entries, load_vault_config, vault_path
import json, re
cfg = load_vault_config()
rows = list_entries(cfg)
blob = json.dumps(rows)
# Fingerprints may start with gsk_/sk- — reject full-length secrets only
SECRET_RE = re.compile(r'(?:gsk_[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9]{20,}|sk-proj-[A-Za-z0-9]{20,})')
m = SECRET_RE.search(blob)
assert not m, f'vault list leaked raw key ({m.group(0)[:16]}...)'
vp = vault_path(cfg)
assert 'data' in str(vp), vp
print('  ok key_vault masked list (' + str(len(rows)) + ' entries)')
"

echo "── Key vault (export deny)"
PYTHONPATH="$ROOT" .venv/bin/python -c "
from modelrouter.key_vault import export_blocked, load_vault_config
cfg = load_vault_config()
assert export_blocked('MODELROUTER_KEY_HERMES', cfg)
assert export_blocked('KRAKEN_API_SECRET', cfg)
assert not export_blocked('GROQ_API_KEY', cfg)
print('  ok key_vault export deny')
"

echo "── Route policy key hints"
PYTHONPATH="$ROOT" .venv/bin/python -c "
from modelrouter.route_policy import recommend
rec = recommend('smalshi-hermes', write_hints=False)
d = rec.to_dict()
assert 'key_hints' in d and isinstance(d['key_hints'], dict)
print('  ok route_policy key_hints')
"

echo "── Key vault rate limit"
PYTHONPATH="$ROOT" .venv/bin/python -c "
from modelrouter.key_vault import env_var_for_model, is_rate_limit_error, record_rate_limit
assert env_var_for_model('groq/llama-3.3-70b') == 'GROQ_API_KEY'
assert is_rate_limit_error('HTTP 429 Too Many Requests')
assert record_rate_limit('unknown/model', '429')['reason'] == 'unknown_model'
print('  ok key_vault rate_limit helpers')
"

echo "── OAuth exchange stub"
PYTHONPATH="$ROOT" .venv/bin/python -c "
from modelrouter.oauth_exchange import new_oauth_state, validate_oauth_state, exchange_google_code
s = new_oauth_state('google_test')
assert validate_oauth_state(s, 'google_test')
assert not validate_oauth_state(s, 'google_test')
stub = exchange_google_code('code123', 'bad')
assert stub.get('error') == 'invalid_state'
print('  ok oauth_exchange state + stub')
"

echo "── Ethereum RPC fallback"
cd "$ROOT/tokens/scripts" && PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
from fetch_wallets import fetch_ethereum_balance_rpc
r = fetch_ethereum_balance_rpc('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045')
assert r.get('status') == 'ok'
assert r.get('native_symbol') == 'ETH'
assert r.get('source') == 'rpc'
print('  ok ethereum rpc fallback')
"

echo "── Vault rotate export helper"
cd "$ROOT" && PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
from modelrouter.key_vault import apply_last_rotate_export
r = apply_last_rotate_export(dry_run=True)
assert r.get('reason') in ('no_hints', 'no_ok_hint') or r.get('ok')
print('  ok vault rotate export helper')
"

echo "── Tangem preset sync"
cd "$ROOT/tokens/scripts" && PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
from fetch_usage import load_config, resolve_secret
from wallet_store import sync_presets_from_config, list_enabled
cfg = load_config()
btc = resolve_secret('TANGEM_BTC_ADDRESS')
sync_presets_from_config(cfg)
n = len([w for w in list_enabled() if 'tangem' in (w.get('label') or '').lower()])
if btc:
    assert n >= 1, 'TANGEM in env but not synced'
    print('  ok tangem presets (' + str(n) + ' wallets)')
else:
    print('  skip tangem presets (TANGEM_* not in env)')
"

echo "── Equity timeout helper"
cd "$ROOT" && PYTHONPATH="$ROOT/tokens/scripts" "$ROOT/.venv/bin/python" -c "
from fetch_equity import read_stale_equity
from fetch_usage import _fetch_equity_safe
assert callable(read_stale_equity)
assert callable(_fetch_equity_safe)
print('  ok equity bounded fetch')
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

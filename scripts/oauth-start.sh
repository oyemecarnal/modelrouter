#!/usr/bin/env bash
# Phase 3 OAuth stub — documents flow; paste-key remains default.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROVIDER="${1:-${PROVIDER:-}}"

usage() {
  echo "Usage: oauth-start.sh <provider>   # e.g. google"
  echo "       make oauth-start PROVIDER=google"
  echo ""
  echo "OAuth connectors are not implemented (Phase 3)."
  echo "Use paste-key instead:"
  echo "  make connect-<provider>   # e.g. make connect-google"
  echo "  Widget: ＋ Provider modal"
  echo ""
  echo "Spec: docs/OAUTH_CONNECTOR_SPEC.md"
  echo "Dev callback listener: OAUTH_STUB_LISTEN=1 make oauth-start PROVIDER=google"
}

if [[ -z "$PROVIDER" || "$PROVIDER" == "-h" || "$PROVIDER" == "--help" ]]; then
  usage
  exit 0
fi

PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -c "
import sys
import yaml
from pathlib import Path
root = Path('$ROOT')
reg = yaml.safe_load((root / 'config/connectors.yaml').read_text()) or {}
conn = (reg.get('connectors') or {}).get('$PROVIDER')
if not conn:
    print('Unknown provider: $PROVIDER', file=sys.stderr)
    print('Available:', ', '.join(sorted((reg.get('connectors') or {}).keys())), file=sys.stderr)
    sys.exit(2)
mode = (conn or {}).get('mode') or 'paste_key'
if mode == 'oauth':
    print('Provider $PROVIDER is marked oauth in registry (future).')
else:
    print('Provider $PROVIDER uses paste-key today (mode=%s).' % mode)
make = (conn or {}).get('make_target') or 'connect-$PROVIDER'
print('Use: make %s' % make)
"

if [[ "${OAUTH_STUB_LISTEN:-}" == 1 ]]; then
  echo ""
  echo "── Callback stub (dev only — does not exchange tokens)"
  exec "$ROOT/.venv/bin/python" "$ROOT/scripts/oauth_callback_stub.py"
fi

exit 2

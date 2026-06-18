#!/usr/bin/env bash
# Generic provider dispatch — lists ids or delegates to connect-key.sh
set -euo pipefail
exec "$(dirname "$0")/connect-key.sh" "$@"

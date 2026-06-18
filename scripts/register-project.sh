#!/usr/bin/env bash
# Register a consumer project in config/projects.yaml (idempotent append).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECTS="$ROOT/config/projects.yaml"

usage() {
  cat <<EOF
Usage: $0 <project-id> [options]

  --description TEXT   Human label (default: project-id)
  --host HOST          Repeatable: laptop, gateway-mini, gateway-tower (default: laptop)
  --routine PRESET     Routine preset (default: cheap)
  --complex PRESET     Complex preset (default: smart)
  --dry-run            Print YAML block only

Examples:
  $0 my-bot --host laptop --host gateway-tower --routine hermes-fast --complex hermes-smart
  make register-project PROJECT=my-bot ROUTINE=cheap

Writes virtual_key_env: MODELROUTER_KEY_<UPPER_ID> (native mode uses master key).
EOF
}

PROJECT_ID="${1:-}"
shift || true
[[ -n "$PROJECT_ID" ]] || { usage >&2; exit 1; }

DESCRIPTION="$PROJECT_ID"
declare -a HOSTS=("laptop")
ROUTINE="cheap"
COMPLEX="smart"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --description) DESCRIPTION="$2"; shift 2 ;;
    --host) HOSTS+=("$2"); shift 2 ;;
    --routine) ROUTINE="$2"; shift 2 ;;
    --complex) COMPLEX="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

# Dedupe hosts, preserve order
UNIQ_HOSTS=()
for h in "${HOSTS[@]}"; do
  skip=0
  for u in "${UNIQ_HOSTS[@]:-}"; do [[ "$u" == "$h" ]] && skip=1 && break; done
  [[ $skip -eq 0 ]] && UNIQ_HOSTS+=("$h")
done

KEY_ENV="MODELROUTER_KEY_$(echo "$PROJECT_ID" | tr '[:lower:]-' '[:upper:]_')"

HOST_YAML=""
for h in "${UNIQ_HOSTS[@]}"; do
  HOST_YAML="${HOST_YAML}      - ${h}"$'\n'
done

BLOCK=$(cat <<EOF

  ${PROJECT_ID}:
    description: ${DESCRIPTION}
    hosts:
$(printf '%s\n' "${UNIQ_HOSTS[@]}" | sed 's/^/      - /')
    presets:
      routine: ${ROUTINE}
      complex: ${COMPLEX}
    virtual_key_env: ${KEY_ENV}
EOF
)

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "$BLOCK"
  exit 0
fi

if grep -qE "^  ${PROJECT_ID}:" "$PROJECTS" 2>/dev/null; then
  echo "[register-project] already registered: ${PROJECT_ID}" >&2
  exit 0
fi

cp "$PROJECTS" "${PROJECTS}.bak"
printf '%s\n' "$BLOCK" >> "$PROJECTS"
echo "[register-project] added ${PROJECT_ID} → ${KEY_ENV}"
echo "  Next: make issue-project-keys  # refresh virtual keys in .env"
echo "  Docs: docs/INTEGRATION.md"

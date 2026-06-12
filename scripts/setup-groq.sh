#!/usr/bin/env bash
# Groq via GitHub login gives you console access — you still need an API key in .env.
# GitHub Actions secrets are write-only; this script helps store the key in both places.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"

echo "==> Groq setup for ModelRouter"
echo ""
echo "1. Sign in at https://console.groq.com (GitHub OAuth works)"
echo "2. Create key: https://console.groq.com/keys  (starts with gsk_)"
echo ""

if [[ -n "${GROQ_API_KEY:-}" ]]; then
  KEY="$GROQ_API_KEY"
  echo "Using GROQ_API_KEY from environment."
elif [[ -f "$ENV_FILE" ]] && grep -q '^GROQ_API_KEY=.' "$ENV_FILE"; then
  echo "GROQ_API_KEY already set in $ENV_FILE"
  exit 0
else
  read -rsp "Paste Groq API key (gsk_...): " KEY
  echo ""
fi

[[ -n "$KEY" ]] || { echo "No key provided." >&2; exit 1; }

python3 - "$ENV_FILE" "$KEY" <<'PY'
import sys
from pathlib import Path
path, key = sys.argv[1:3]
lines = Path(path).read_text().splitlines() if Path(path).exists() else []
out, done = [], False
for line in lines:
    if line.startswith("GROQ_API_KEY="):
        out.append(f"GROQ_API_KEY={key}")
        done = True
    else:
        out.append(line)
if not done:
    out.append(f"GROQ_API_KEY={key}")
Path(path).write_text("\n".join(out) + "\n")
PY

echo "==> Saved to $ENV_FILE"

if gh auth status &>/dev/null; then
  read -rp "Also store in GitHub repo secret? Enter repo (owner/name) or skip: " REPO
  if [[ -n "$REPO" ]]; then
    gh secret set GROQ_API_KEY --body "$KEY" -R "$REPO"
    echo "==> Stored GROQ_API_KEY in GitHub Actions secrets for $REPO"
  fi
else
  echo "==> gh not logged in — skip GitHub secret storage"
fi

echo "==> Restart: make restart"

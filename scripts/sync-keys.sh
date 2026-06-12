#!/usr/bin/env bash
# Fill empty entries in modelrouter/.env from other known project env files.
# Never overwrites existing values. Never prints secret values.
# Bash 3.2 compatible (macOS default).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
DRY_RUN=false
USE_MINI=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --from-mini) USE_MINI=true ;;
  esac
done

get_val() {
  local key="$1" file="$2"
  [[ -f "$file" ]] || return 1
  local line val
  line=$(grep -E "^${key}=" "$file" 2>/dev/null | tail -1) || return 1
  val="${line#*=}"
  val="${val%\"}"; val="${val#\"}"; val="${val%\'}"; val="${val#\'}"
  [[ -n "$val" ]] || return 1
  echo "$val"
}

get_val_zshrc() {
  local key="$1"
  [[ -f "$HOME/.zshrc" ]] || return 1
  local line val
  line=$(grep -E "^export ${key}=" "$HOME/.zshrc" 2>/dev/null | tail -1) || return 1
  val="${line#export ${key}=}"
  val="${val%\"}"; val="${val#\"}"; val="${val%\'}"; val="${val#\'}"
  [[ -n "$val" ]] || return 1
  echo "$val"
}

resolve_key() {
  local key="$1" val="" src
  local -a sources=(
    "$HOME/dev/smalshi/.env"
    "$HOME/dev/smalshi/Codex/.env"
    "$HOME/dev/coinbot/.env"
    "$HOME/dev/Kalshi_bot/.env"
    "$HOME/dev/project_kc/signals/.env"
  )

  if $USE_MINI && [[ -f "${REMOTE_ENV:-}" ]]; then
    sources=("$REMOTE_ENV" "${sources[@]}")
  fi

  if [[ "$key" == "GOOGLE_API_KEY" || "$key" == "GEMINI_API_KEY" ]]; then
    for src in "${sources[@]}"; do
      val=$(get_val "GOOGLE_API_KEY" "$src" 2>/dev/null) && break
      val=$(get_val "GEMINI_API_KEY" "$src" 2>/dev/null) && break
    done
  else
    for src in "${sources[@]}"; do
      val=$(get_val "$key" "$src" 2>/dev/null) && break
    done
    if [[ -z "$val" ]]; then
      val=$(get_val_zshrc "$key" 2>/dev/null || true)
    fi
  fi
  [[ -n "${val:-}" ]] && echo "$val"
}

KEYS="OPENAI_API_KEY ANTHROPIC_API_KEY GOOGLE_API_KEY GEMINI_API_KEY OPENROUTER_API_KEY CURSOR_API_KEY POLYGON_API_KEY GROQ_API_KEY TOGETHER_API_KEY MISTRAL_API_KEY COHERE_API_KEY DEEPSEEK_API_KEY XAI_API_KEY HUGGINGFACE_API_KEY FIREWORKS_API_KEY PERPLEXITY_API_KEY"

REMOTE_ENV=""
if $USE_MINI; then
  echo "[sync-keys] Pulling kc-mini ~/dev/modelrouter/.env snapshot..."
  REMOTE_ENV=$(mktemp)
  scp kc-mini-lan:~/dev/modelrouter/.env "$REMOTE_ENV" 2>/dev/null || true
fi

[[ -f "$ENV_FILE" ]] || cp "$ROOT/.env.example" "$ENV_FILE"

UPDATED=0
for key in $KEYS; do
  current=$(get_val "$key" "$ENV_FILE" 2>/dev/null || true)
  [[ -n "$current" ]] && continue
  found=$(resolve_key "$key" 2>/dev/null || true)
  [[ -z "$found" ]] && continue

  echo "  + $key"
  UPDATED=$((UPDATED + 1))

  if ! $DRY_RUN; then
    if grep -q "^${key}=" "$ENV_FILE"; then
      python3 - "$ENV_FILE" "$key" "$found" <<'PY'
import sys
from pathlib import Path
path, key, val = sys.argv[1:4]
lines = Path(path).read_text().splitlines()
out, done = [], False
for line in lines:
    if line.startswith(key + "="):
        out.append(f"{key}={val}")
        done = True
    else:
        out.append(line)
if not done:
    out.append(f"{key}={val}")
Path(path).write_text("\n".join(out) + "\n")
PY
    else
      echo "${key}=${found}" >> "$ENV_FILE"
    fi
  fi
done

if [[ $UPDATED -eq 0 ]]; then
  echo "[sync-keys] Nothing to fill — all tracked keys already set or not found elsewhere."
else
  if $DRY_RUN; then
    echo "[sync-keys] Dry run — would set $UPDATED key(s). No changes written."
  else
    echo "[sync-keys] Set $UPDATED key(s) in $ENV_FILE. Restart: make restart"
  fi
fi

[[ -n "$REMOTE_ENV" ]] && rm -f "$REMOTE_ENV"
exit 0

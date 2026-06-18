#!/usr/bin/env bash
# Trim large gitignored logs under data/ (keeps last N lines).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KEEP="${MODELROUTER_LOG_KEEP_LINES:-10000}"
MAX_MB="${MODELROUTER_LOG_TRIM_MB:-50}"

ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

echo "==> Trim logs (keep last ${KEEP} lines, trim if > ${MAX_MB}MB)"
max_bytes=$((MAX_MB * 1024 * 1024))
trimmed=0

for rel in modelrouter.log launchd.stdout.log launchd.stderr.log; do
  f="$ROOT/data/$rel"
  [[ -f "$f" ]] || continue
  size="$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null || echo 0)"
  if [[ "$size" -le "$max_bytes" ]]; then
    ok "$rel (${size} bytes) — ok"
    continue
  fi
  tmp="$(mktemp)"
  tail -n "$KEEP" "$f" > "$tmp"
  mv "$tmp" "$f"
  new_size="$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null || echo 0)"
  warn "$rel trimmed ${size} → ${new_size} bytes"
  trimmed=$((trimmed + 1))
done

if [[ "$trimmed" -eq 0 ]]; then
  ok "no logs needed trimming"
else
  ok "trimmed ${trimmed} log file(s)"
fi

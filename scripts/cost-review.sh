#!/usr/bin/env bash
# Periodic cost review — surfaces cheaper alternatives and routing hints.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/lib.sh"
modelrouter_load_env

echo "==> ModelRouter cost review"
echo "    $(date '+%Y-%m-%d %H:%M')"
echo ""
echo "── Core question"
echo "  Is there already a better tool — cheaper or saves model use?"
echo "  If yes → use it. ModelRouter only for what still needs an LLM."
echo ""

echo "── Quick health"
if MODELROUTER_ROOT="$ROOT" "$ROOT/scripts/healthcheck.sh" &>/dev/null; then
  echo "  Gateway: up"
else
  echo "  Gateway: DOWN (fix before optimizing spend)"
fi

echo ""
echo "── Route hints (widget → presets)"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -m modelrouter.route_policy --project smalshi-hermes 2>/dev/null | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"  Hermes → {d['preset']}: {d['reason']}\")" || true
  PYTHONPATH="$ROOT" "$ROOT/.venv/bin/python" -m modelrouter.route_policy --project kalshi-bot 2>/dev/null | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"  Kalshi → {d['preset']}: {d['reason']}\")" || true
else
  echo "  (run make install for route hints)"
fi

echo ""
echo "── Alternatives catalog (config/cost_alternatives.yaml)"
python3 <<PY
import yaml
from pathlib import Path
p = Path("$ROOT/config/cost_alternatives.yaml")
data = yaml.safe_load(p.read_text()) if p.exists() else {}
for alt in (data.get("alternatives") or [])[:6]:
    print(f"  • {alt.get('instead_of')}")
    print(f"    → {alt.get('use')}")
print(f"  … see docs/COST_REVIEW.md (+{max(0,len(data.get('alternatives',[]))-6)} more)")
PY

echo ""
echo "── Checklist (answer honestly)"
cat <<'EOF'
  [ ] Any new job still using model: smart? Try cheap / hermes-fast / code first.
  [ ] Any loop that could be a script, cron, or make doctor? Remove the LLM call.
  [ ] Codex/Cursor quota hot? (Keys widget) → downshift presets today.
  [ ] OpenRouter still stubbed? Good — only enable if you need an exotic model.
  [ ] Tower bots using mini gateway? (one key store, not duplicated .env)
  [ ] Worth paying for something new? Write one line in data/cost_review_log.md
EOF

LOG="$ROOT/data/cost_review_log.md"
if [[ ! -f "$LOG" ]]; then
  mkdir -p "$ROOT/data"
  cat >"$LOG" <<'EOF'
# Cost review log

| Date | Considered | Decision | Notes |
|------|------------|----------|-------|
EOF
  echo "  Created $LOG — append rows after each review"
fi

echo ""
echo "── Docs: docs/COST_REVIEW.md"

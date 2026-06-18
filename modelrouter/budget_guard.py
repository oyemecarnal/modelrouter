"""
Budget threshold guard — fires macOS notifications when LLM spend crosses configured limits.

Called automatically at the end of each cost rollup (via fetch_usage.py snapshot build).
Tracks which thresholds have already been notified to avoid notification spam.

Config (tokens/config.json → "budgets" key):
    {
      "budgets": {
        "daily":   {"warn": 0.50, "hard": 2.00},
        "weekly":  {"warn": 3.00, "hard": 10.00},
        "monthly": {"warn": 10.00, "hard": 40.00}
      }
    }

State file: data/budget_notify_state.json
  Tracks last-notified amounts per window so warn only fires once per crossing,
  not on every snapshot refresh.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "data" / "budget_notify_state.json"

# Rollup window label → config key
_WINDOW_MAP = {
    "24h": "daily",
    "7d":  "weekly",
    "30d": "monthly",
}

_DEFAULT_STATE: dict[str, Any] = {
    "notified_warn": {},   # window → last_spend_at_notification
    "notified_hard": {},
    "last_checked": None,
}


# ── State I/O ─────────────────────────────────────────────────────────────────

def _read_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return dict(_DEFAULT_STATE)
    try:
        return {**_DEFAULT_STATE, **json.loads(STATE_PATH.read_text())}
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_STATE)


def _write_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state["last_checked"] = int(time.time())
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


# ── Notification ──────────────────────────────────────────────────────────────

def _notify(title: str, message: str, subtitle: str = "ModelRouter") -> None:
    """Fire a macOS notification via osascript (no external deps)."""
    script = (
        f'display notification "{message}" '
        f'with title "{title}" '
        f'subtitle "{subtitle}"'
    )
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=False,
            capture_output=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # non-macOS or osascript unavailable — silent


def _fmt_usd(amount: float) -> str:
    if amount < 0.01:
        return f"${amount:.4f}"
    return f"${amount:.2f}"


# ── Threshold checker ─────────────────────────────────────────────────────────

# How far above a threshold the spend must be before re-notifying (avoid
# double-notify when spend oscillates right around the threshold).
_RENOTIFY_MARGIN = 0.10  # 10% above last notified amount


def check(
    rollup: dict[str, Any],
    budgets: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Compare rollup spend against budget thresholds and fire notifications.

    rollup:  output of modelrouter.cost_rollup.rollup()
    budgets: the "budgets" block from tokens/config.json

    Returns a list of firing events (for inclusion in snapshot).
    """
    if not budgets:
        return []

    windows: dict[str, dict[str, float]] = rollup.get("windows") or {}
    state = _read_state()
    events: list[dict[str, Any]] = []

    for rollup_label, config_key in _WINDOW_MAP.items():
        cfg = budgets.get(config_key)
        if not cfg:
            continue
        spend = float((windows.get(rollup_label) or {}).get("total_usd") or 0)
        warn_limit = float(cfg.get("warn") or 0)
        hard_limit = float(cfg.get("hard") or 0)

        # --- hard limit ---
        if hard_limit and spend >= hard_limit:
            last = float(state["notified_hard"].get(rollup_label) or 0)
            if spend >= last * (1 + _RENOTIFY_MARGIN) or last == 0:
                _notify(
                    title="⛔ ModelRouter Budget Exceeded",
                    message=(
                        f"{_fmt_usd(spend)} spent in the last {rollup_label} "
                        f"— hard limit is {_fmt_usd(hard_limit)}"
                    ),
                )
                state["notified_hard"][rollup_label] = spend
                events.append({
                    "level": "hard",
                    "window": rollup_label,
                    "spend": spend,
                    "limit": hard_limit,
                })

        # --- warn limit (only if hard not also firing) ---
        elif warn_limit and spend >= warn_limit:
            last = float(state["notified_warn"].get(rollup_label) or 0)
            if spend >= last * (1 + _RENOTIFY_MARGIN) or last == 0:
                pct = int(spend / warn_limit * 100)
                _notify(
                    title="⚠️ ModelRouter Budget Warning",
                    message=(
                        f"{_fmt_usd(spend)} of {_fmt_usd(warn_limit)} "
                        f"{config_key} budget used ({pct}%)"
                    ),
                )
                state["notified_warn"][rollup_label] = spend
                events.append({
                    "level": "warn",
                    "window": rollup_label,
                    "spend": spend,
                    "limit": warn_limit,
                    "pct": pct,
                })

        else:
            # Spend dropped back below warn — reset so next crossing re-notifies
            if rollup_label in state["notified_warn"]:
                del state["notified_warn"][rollup_label]
            if rollup_label in state["notified_hard"]:
                del state["notified_hard"][rollup_label]

    _write_state(state)
    return events


# ── Convenience wrapper (called from fetch_usage.py) ─────────────────────────

def check_from_config(rollup: dict[str, Any], widget_config: dict[str, Any]) -> list[dict[str, Any]]:
    """Load budget thresholds from widget config and run check()."""
    budgets = widget_config.get("budgets") or {}
    if not budgets:
        return []
    return check(rollup, budgets)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys as _sys

    _sys.path.insert(0, str(ROOT))
    from modelrouter.cost_rollup import rollup as _rollup

    parser = argparse.ArgumentParser(description="Budget guard — check thresholds and notify")
    parser.add_argument("--daily-warn",   type=float, default=0.50)
    parser.add_argument("--daily-hard",   type=float, default=2.00)
    parser.add_argument("--weekly-warn",  type=float, default=3.00)
    parser.add_argument("--weekly-hard",  type=float, default=10.00)
    parser.add_argument("--monthly-warn", type=float, default=10.00)
    parser.add_argument("--monthly-hard", type=float, default=40.00)
    parser.add_argument("--reset",        action="store_true", help="Reset notification state")
    args = parser.parse_args()

    if args.reset:
        STATE_PATH.unlink(missing_ok=True)
        print("Notification state reset.")
        raise SystemExit(0)

    budgets = {
        "daily":   {"warn": args.daily_warn,   "hard": args.daily_hard},
        "weekly":  {"warn": args.weekly_warn,   "hard": args.weekly_hard},
        "monthly": {"warn": args.monthly_warn,  "hard": args.monthly_hard},
    }
    data = _rollup()
    events = check(data, budgets)
    print(json.dumps({"rollup_windows": data["windows"], "events": events}, indent=2))

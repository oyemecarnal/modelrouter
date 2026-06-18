"""Aggregate cost/token spend from ModelRouter JSON logs."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG = ROOT / "data" / "modelrouter.log"

WINDOWS: list[tuple[str, float]] = [
    ("1h", 1.0),
    ("24h", 24.0),
    ("7d", 168.0),
    ("30d", 720.0),
]


def _cutoff(hours: float) -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=hours)


def _provider(model: str) -> str:
    """Best-effort provider label from a model string like 'groq/llama-3.3-70b-versatile'."""
    if "/" in model:
        return model.split("/")[0]
    for prefix in ("gpt-", "o1", "o3"):
        if model.startswith(prefix):
            return "openai"
    if model.startswith("claude"):
        return "anthropic"
    return model


def rollup(log_path: Path = DEFAULT_LOG) -> dict[str, Any]:
    if not log_path.exists():
        return _empty()

    now = datetime.now(timezone.utc)
    oldest_hours = WINDOWS[-1][1]
    oldest_cutoff = now - timedelta(hours=oldest_hours)

    # model → window_label → {cost_usd, tokens, input_tokens, output_tokens, requests}
    by_model: dict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: {
            label: {"cost_usd": 0.0, "tokens": 0, "input_tokens": 0, "output_tokens": 0, "requests": 0}
            for label, _ in WINDOWS
        }
    )

    try:
        lines = log_path.read_text(errors="replace").splitlines()
    except OSError:
        return _empty()

    for line in lines:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("event") != "request_success":
            continue
        ts_str = row.get("ts")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts < oldest_cutoff:
            continue

        model = (row.get("model") or "unknown").strip()
        cost = float(row.get("cost_usd") or 0)
        tokens = int(row.get("tokens") or 0)
        input_tok = int(row.get("input_tokens") or 0)
        output_tok = int(row.get("output_tokens") or 0)
        age_hours = (now - ts).total_seconds() / 3600

        for label, max_hours in WINDOWS:
            if age_hours <= max_hours:
                bucket = by_model[model][label]
                bucket["cost_usd"] += cost
                bucket["tokens"] += tokens
                bucket["input_tokens"] += input_tok
                bucket["output_tokens"] += output_tok
                bucket["requests"] += 1

    windows_summary: dict[str, dict[str, Any]] = {}
    by_model_out: dict[str, list[dict[str, Any]]] = {}

    for label, _ in WINDOWS:
        total_cost = 0.0
        total_req = 0
        total_tok = 0
        rows = []
        for model, wmap in by_model.items():
            b = wmap[label]
            if b["requests"] == 0:
                continue
            total_cost += b["cost_usd"]
            total_req += b["requests"]
            total_tok += b["tokens"]
            rows.append(
                {
                    "model": model,
                    "provider": _provider(model),
                    "cost_usd": round(b["cost_usd"], 6),
                    "tokens": b["tokens"],
                    "input_tokens": b["input_tokens"],
                    "output_tokens": b["output_tokens"],
                    "requests": b["requests"],
                }
            )
        rows.sort(key=lambda r: -r["cost_usd"])
        windows_summary[label] = {
            "total_usd": round(total_cost, 6),
            "requests": total_req,
            "tokens": total_tok,
        }
        by_model_out[label] = rows[:20]

    import time

    return {
        "updated_at": int(time.time() * 1000),
        "windows": windows_summary,
        "by_model": by_model_out,
    }


def _empty() -> dict[str, Any]:
    import time

    return {
        "updated_at": int(time.time() * 1000),
        "windows": {label: {"total_usd": 0.0, "requests": 0, "tokens": 0} for label, _ in WINDOWS},
        "by_model": {label: [] for label, _ in WINDOWS},
        "no_data": True,
    }


if __name__ == "__main__":
    import sys

    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LOG
    print(json.dumps(rollup(path), indent=2))

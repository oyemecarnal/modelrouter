#!/usr/bin/env python3
"""Summarize ModelRouter JSON log lines by model/preset."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG = ROOT / "data" / "modelrouter.log"


def parse_log(path: Path, hours: float | None) -> dict[str, dict[str, int | float]]:
    from datetime import datetime, timedelta, timezone

    cutoff = None
    if hours is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    by_model: dict[str, dict[str, int | float]] = defaultdict(
        lambda: {"requests": 0, "success": 0, "failure": 0, "tokens": 0, "duration_ms": 0.0}
    )

    if not path.exists():
        return {}

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if cutoff and row.get("ts"):
            try:
                ts = datetime.fromisoformat(row["ts"].replace("Z", "+00:00"))
                if ts < cutoff:
                    continue
            except ValueError:
                pass
        event = row.get("event")
        model = row.get("model") or "unknown"
        bucket = by_model[model]
        if event == "request_start":
            bucket["requests"] += 1
        elif event == "request_success":
            bucket["success"] += 1
            if row.get("tokens"):
                bucket["tokens"] += int(row["tokens"])
            if row.get("duration_ms"):
                bucket["duration_ms"] += float(row["duration_ms"])
        elif event == "request_failure":
            bucket["failure"] += 1

    return dict(by_model)


def main() -> int:
    parser = argparse.ArgumentParser(description="ModelRouter usage rollup from JSON logs")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--hours", type=float, default=24.0, help="Lookback window (default 24h)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    stats = parse_log(args.log, args.hours)
    if args.json:
        print(json.dumps(stats, indent=2))
        return 0

    print(f"==> Usage rollup ({args.hours}h) — {args.log}")
    if not stats:
        print("  (no JSON events — run gateway traffic; callback logs to stdout in log file)")
        return 0

    rows = sorted(stats.items(), key=lambda x: (-int(x[1]["success"]), x[0]))
    for model, s in rows:
        tok = int(s["tokens"])
        dur = float(s["duration_ms"])
        print(
            f"  {model:28}  ok={s['success']:3}  fail={s['failure']:2}  "
            f"tokens={tok:6}  avg_ms={dur / max(int(s['success']), 1):.0f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

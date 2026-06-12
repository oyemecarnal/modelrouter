"""Fetch exchange equity via coinbot (local or kc-mini SSH). Read-only balances."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
EQUITY_CACHE = Path.home() / "Library/Application Support/TokenWidget/equity_cache.json"


def _default_cfg() -> dict[str, Any]:
    return {
        "enabled": True,
        "remote_host": os.environ.get("MODELROUTER_REMOTE_HOST", "kc-mini-lan"),
        "coinbot_root": str(Path.home() / "dev" / "coinbot"),
        "brokers": ["kraken", "coinbase"],
        "prefer_remote": True,
        "force_live": True,
        "cache_ttl_seconds": 300,
        "timeout_seconds": 45,
        "instance_id": "phase1_paper_daily",
    }


def fetch_equity(cfg: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Return equity payload or None when disabled."""
    base = _default_cfg()
    if cfg:
        equity_cfg = cfg.get("equity") or {}
        if isinstance(equity_cfg, dict):
            base.update(equity_cfg)

    if not base.get("enabled", True):
        return None

    cache_ttl = int(base.get("cache_ttl_seconds") or 0)
    if cache_ttl > 0:
        cached = _read_cache(cache_ttl)
        if cached:
            cached["cached"] = True
            return cached

    brokers = base.get("brokers") or ["kraken", "coinbase"]
    broker_arg = ",".join(brokers)
    coinbot_root = Path(base["coinbot_root"])
    prefer_remote = base.get("prefer_remote", True)
    remote_host = base.get("remote_host", "kc-mini-lan")
    force_live = base.get("force_live", True)
    timeout_sec = float(base.get("timeout_seconds") or 75)
    instance_id = base.get("instance_id") or "phase1_paper_daily"

    local_brokers = [b.lower() for b in (base.get("local_brokers") or [])]
    remote_brokers = [b.lower() for b in (base.get("remote_brokers") or brokers)]

    if prefer_remote and remote_host:
        status = _fetch_status_remote(remote_host, instance_id)
        if status:
            return status

    broker_rows: list[dict[str, Any]] = []
    errors: list[str] = []

    if local_brokers and coinbot_root.is_dir():
        local_arg = ",".join(local_brokers)
        try:
            local_payload = _fetch_local(coinbot_root, local_arg, force_live, timeout_sec)
            broker_rows.extend(local_payload.get("brokers") or [])
        except Exception as exc:
            errors.append(f"local: {exc}")

    remote_to_fetch = [b for b in remote_brokers if b not in {r.get("broker") for r in broker_rows if r.get("status") == "ok"}]
    if remote_to_fetch and prefer_remote and remote_host:
        remote_arg = ",".join(remote_to_fetch)
        try:
            remote_payload = _fetch_remote(remote_host, coinbot_root, remote_arg, force_live, timeout_sec)
            broker_rows.extend(remote_payload.get("brokers") or [])
            if remote_payload.get("error"):
                errors.append(str(remote_payload["error"]))
        except Exception as exc:
            errors.append(f"remote: {exc}")
    elif not broker_rows and coinbot_root.is_dir():
        payload = _fetch_local(coinbot_root, broker_arg, force_live, timeout_sec)
        broker_rows = payload.get("brokers") or []
    elif not broker_rows:
        payload = {
            "updated_at": None,
            "source": "coinbot",
            "host": None,
            "total_equity_usd": None,
            "brokers": [],
            "error": "coinbot not found locally and remote disabled",
        }
        if errors:
            payload["error"] = "; ".join(errors)
        return payload

    total = sum(r["equity_usd"] or 0 for r in broker_rows if r.get("status") == "ok")
    payload = {
        "updated_at": int(time.time() * 1000),
        "source": "coinbot",
        "host": remote_host if prefer_remote else "local",
        "total_equity_usd": round(total, 2) if total else None,
        "brokers": broker_rows,
    }
    if errors:
        payload["error"] = "; ".join(errors)

    if payload and any(b.get("status") == "ok" for b in payload.get("brokers", [])):
        _write_cache(payload)
    elif cache_ttl > 0:
        stale = _read_cache(0)
        if stale:
            stale["cached"] = True
            stale["stale"] = True
            return stale
    return payload


def _read_cache(ttl_seconds: int) -> dict[str, Any] | None:
    if not EQUITY_CACHE.exists():
        return None
    try:
        data = json.loads(EQUITY_CACHE.read_text())
        age_ms = int(time.time() * 1000) - int(data.get("updated_at") or 0)
        if ttl_seconds > 0 and age_ms > ttl_seconds * 1000:
            return None
        return data
    except Exception:
        return None


def _write_cache(payload: dict[str, Any]) -> None:
    try:
        EQUITY_CACHE.parent.mkdir(parents=True, exist_ok=True)
        EQUITY_CACHE.write_text(json.dumps(payload, indent=2))
    except OSError:
        pass


def _status_to_equity(status: dict[str, Any], host: str) -> dict[str, Any]:
    equity = status.get("total_equity_usd") or status.get("equity_usd")
    broker = (status.get("broker") or status.get("exchange") or "coinbot").lower()
    assets = []
    for asset, bal in (status.get("balances") or {}).items():
        if isinstance(bal, dict):
            total = float(bal.get("total") or 0)
        else:
            total = float(bal or 0)
        if total <= 0:
            continue
        assets.append({"asset": asset, "amount": total, "value_usd": None})
    return {
        "updated_at": int(time.time() * 1000),
        "source": "coinbot-status",
        "host": host,
        "total_equity_usd": round(float(equity), 2) if equity is not None else None,
        "brokers": [
            {
                "broker": broker,
                "status": "ok" if equity is not None else "unavailable",
                "equity_usd": round(float(equity), 2) if equity is not None else None,
                "assets": assets[:6],
                "error": None if equity is not None else "status cache missing equity",
            }
        ],
    }


def _fetch_status_remote(host: str, instance_id: str) -> dict[str, Any] | None:
    remote_path = f"/Users/kevinreed/dev/coinbot/coinbot_v2/data/{instance_id}/status.json"
    proc = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=8", host, f"test -f '{remote_path}' && cat '{remote_path}'"],
        capture_output=True,
        text=True,
        timeout=12,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        status = json.loads(proc.stdout)
        return _status_to_equity(status, host)
    except json.JSONDecodeError:
        return None


def _parse_json(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    if not text:
        raise ValueError("empty equity response")
    return json.loads(text)


def _coinbot_python(coinbot_root: Path) -> str:
    for rel in ("venv/bin/python3", ".venv/bin/python3"):
        candidate = coinbot_root / rel
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def _fetch_local(
    coinbot_root: Path, broker_arg: str, force_live: bool, timeout_sec: float
) -> dict[str, Any]:
    runner = SCRIPTS / "equity_remote_runner.py"
    env = {**os.environ, "COINBOT_ROOT": str(coinbot_root)}
    py = _coinbot_python(coinbot_root)
    cmd = [py, str(runner), "--brokers", broker_arg, "--timeout", str(timeout_sec)]
    if force_live:
        cmd.append("--force-live")
    proc = subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=int(timeout_sec) + 30, cwd=coinbot_root
    )
    if proc.returncode != 0 and not proc.stdout.strip():
        return {
            "updated_at": None,
            "source": "coinbot",
            "host": "local",
            "total_equity_usd": None,
            "brokers": [],
            "error": (proc.stderr or "equity fetch failed")[:300],
        }
    return _parse_json(proc.stdout)


def _fetch_remote(
    host: str, coinbot_root: Path, broker_arg: str, force_live: bool, timeout_sec: float
) -> dict[str, Any]:
    remote_dir = Path(os.environ.get("MODELROUTER_REMOTE_DIR", "/Users/kevinreed/dev/modelrouter"))
    remote_runner = remote_dir / "tokens/scripts/equity_remote_runner.py"
    remote_coinbot = coinbot_root

    rsync_cmd = [
        "rsync",
        "-az",
        str(SCRIPTS / "equity_remote_runner.py"),
        f"{host}:{remote_runner}",
    ]
    subprocess.run(rsync_cmd, capture_output=True, text=True, timeout=30)

    py_venv = f"{remote_coinbot}/venv/bin/python3"
    py_alt = f"{remote_coinbot}/.venv/bin/python3"
    live = " --force-live" if force_live else ""
    remote_cmd = (
        f"COINBOT_ROOT='{remote_coinbot}' bash -lc '"
        f"PY=python3; "
        f"test -x \"{py_venv}\" && PY=\"{py_venv}\"; "
        f"test -x \"{py_alt}\" && PY=\"{py_alt}\"; "
        f"exec \"$PY\" \"{remote_runner}\" --brokers \"{broker_arg}\" "
        f"--timeout {timeout_sec}{live}'"
    )
    proc = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", host, remote_cmd],
        capture_output=True,
        text=True,
        timeout=int(timeout_sec * len(broker_arg.split(","))) + 45,
    )
    if proc.returncode != 0 and not proc.stdout.strip():
        err = (proc.stderr or proc.stdout or "remote equity failed").strip()
        return {
            "updated_at": None,
            "source": "coinbot",
            "host": host,
            "total_equity_usd": None,
            "brokers": [],
            "error": err[:300],
        }
    try:
        return _parse_json(proc.stdout)
    except Exception as exc:
        return {
            "updated_at": None,
            "source": "coinbot",
            "host": host,
            "total_equity_usd": None,
            "brokers": [],
            "error": f"parse error: {exc}",
        }

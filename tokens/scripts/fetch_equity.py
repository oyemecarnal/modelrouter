"""Fetch portfolio equity: exchanges (coinbot), Kalshi, and watch-only wallets."""

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

COINBOT_BROKERS = frozenset({"kraken", "coinbase", "alpaca"})


def _default_cfg() -> dict[str, Any]:
    return {
        "enabled": True,
        "remote_host": os.environ.get("MODELROUTER_REMOTE_HOST", "kc-mini-lan"),
        "coinbot_root": str(Path.home() / "dev" / "coinbot"),
        "brokers": ["kraken", "coinbase", "kalshi"],
        "prefer_remote": True,
        "force_live": True,
        "cache_ttl_seconds": 300,
        "timeout_seconds": 90,
        "instance_id": "phase1_paper_daily",
        "kraken_market_symbols": "BTC/USD,ETH/USD,SOL/USD,USD",
        "broker_timeouts": {"kraken": 120},
    }


def _broker_route(broker: str, base: dict[str, Any]) -> dict[str, Any]:
    """Resolve host, coinbot root, and options for one broker."""
    broker = broker.lower()
    routes = base.get("broker_routes") or {}
    route = dict(routes.get(broker) or {})
    local_brokers = [b.lower() for b in (base.get("local_brokers") or [])]
    remote_brokers = [b.lower() for b in (base.get("remote_brokers") or base.get("brokers") or [])]

    if "remote" not in route:
        route["remote"] = broker in remote_brokers and broker not in local_brokers

    remote_host = base.get("remote_host", "kc-mini-lan")
    if route.get("remote"):
        route.setdefault("host", remote_host)
    else:
        route.setdefault("host", "local")

    route.setdefault("coinbot_root", base.get("coinbot_root"))
    route.setdefault(
        "instance_id",
        base.get("kraken_instance_id") if broker == "kraken" else base.get("instance_id"),
    )
    timeouts = base.get("broker_timeouts") or {}
    route.setdefault("timeout_seconds", timeouts.get(broker) or base.get("timeout_seconds") or 90)
    if broker == "kraken":
        route.setdefault("market_symbols", base.get("kraken_market_symbols"))
    route.setdefault("provider", "kalshi" if broker == "kalshi" else "coinbot")
    return route


def _provider_for(broker: str, base: dict[str, Any]) -> str:
    routes = base.get("broker_routes") or {}
    route = routes.get(broker.lower()) or {}
    return str(route.get("provider") or ("kalshi" if broker == "kalshi" else "coinbot"))


def fetch_equity(cfg: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Return equity payload or None when disabled."""
    base = _default_cfg()
    if cfg:
        equity_cfg = cfg.get("equity") or {}
        if isinstance(equity_cfg, dict):
            base.update(equity_cfg)
        if cfg.get("dev_root"):
            base["dev_root"] = cfg["dev_root"]

    if not base.get("enabled", True):
        return None

    cache_ttl = int(base.get("cache_ttl_seconds") or 0)
    if cache_ttl > 0:
        cached = _read_cache(cache_ttl)
        if cached:
            cached["cached"] = True
            return cached

    brokers = [b.lower() for b in (base.get("brokers") or ["kraken", "coinbase"])]
    prefer_remote = base.get("prefer_remote", True)
    remote_host = base.get("remote_host", "kc-mini-lan")
    force_live = base.get("force_live", True)
    instance_id = base.get("instance_id") or "phase1_paper_daily"

    if prefer_remote and remote_host and not force_live:
        status = _fetch_status_remote(remote_host, instance_id)
        if status:
            return status

    broker_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    hosts_used: list[str] = []

    for broker in brokers:
        provider = _provider_for(broker, base)
        if provider == "kalshi":
            try:
                from equity_kalshi import fetch_kalshi_equity

                row = fetch_kalshi_equity(cfg or {"equity": base, "dev_root": base.get("dev_root")})
                broker_rows.append(row)
                if row.get("host"):
                    hosts_used.append(str(row["host"]))
            except Exception as exc:
                errors.append(f"{broker}: {exc}")
            continue

        route = _broker_route(broker, base)
        host = route.get("host") or "local"
        coinbot_root = Path(route.get("coinbot_root") or base["coinbot_root"])
        timeout_sec = float(route.get("timeout_seconds") or 90)
        inst = route.get("instance_id") or instance_id
        market_symbols = route.get("market_symbols")

        try:
            if route.get("remote") and host not in ("local", ""):
                _sync_master_key(host, inst, route)
                payload = _fetch_remote(
                    host,
                    coinbot_root,
                    broker,
                    force_live,
                    timeout_sec,
                    instance_id=inst,
                    market_symbols=market_symbols,
                )
                hosts_used.append(host)
            elif coinbot_root.is_dir():
                payload = _fetch_local(
                    coinbot_root,
                    broker,
                    force_live,
                    timeout_sec,
                    instance_id=inst,
                    market_symbols=market_symbols,
                )
                hosts_used.append("local")
            else:
                errors.append(f"{broker}: coinbot not found at {coinbot_root}")
                continue

            for row in payload.get("brokers") or []:
                if row.get("broker") == broker:
                    row.setdefault("host", host if route.get("remote") else "local")
                    row.setdefault("type", "exchange")
                    broker_rows.append(row)
                    break
            if payload.get("error"):
                errors.append(f"{broker}: {payload['error']}")
        except Exception as exc:
            errors.append(f"{broker}: {exc}")

    if base.get("include_wallets", True):
        try:
            from fetch_wallets import wallet_equity_rows

            wallet_cfg = {
                "dev_root": base.get("dev_root") or (cfg or {}).get("dev_root"),
                "wallets": (cfg or {}).get("wallets") or {},
                "equity": base,
            }
            for row in wallet_equity_rows(wallet_cfg):
                broker_rows.append(row)
                hosts_used.append("on-chain")
        except Exception as exc:
            errors.append(f"wallets: {exc}")

    if not broker_rows:
        payload = {
            "updated_at": int(time.time() * 1000),
            "source": "coinbot",
            "host": hosts_used[0] if hosts_used else None,
            "total_equity_usd": None,
            "brokers": [],
            "error": "; ".join(errors) if errors else "no broker data",
        }
        return payload

    ok_rows = [r for r in broker_rows if r.get("status") == "ok"]
    total = sum(r.get("equity_usd") or 0 for r in ok_rows)
    by_type: dict[str, float] = {}
    for row in ok_rows:
        kind = row.get("type") or "exchange"
        by_type[kind] = by_type.get(kind, 0.0) + (row.get("equity_usd") or 0)

    payload = {
        "updated_at": int(time.time() * 1000),
        "source": "portfolio",
        "host": hosts_used[0] if len(set(hosts_used)) == 1 else "multi",
        "total_equity_usd": round(total, 2) if total else None,
        "breakdown": {k: round(v, 2) for k, v in by_type.items()},
        "brokers": broker_rows,
    }
    if errors:
        payload["error"] = "; ".join(errors)

    if ok_rows:
        _write_cache(payload)
    elif cache_ttl > 0:
        stale = _read_cache(0)
        if stale:
            stale["cached"] = True
            stale["stale"] = True
            return stale
    return payload


def _sync_master_key(host: str, instance_id: str | None, route: dict[str, Any]) -> None:
    """Optional: rsync coinbot master key to remote host before encrypted-key decrypt."""
    if not instance_id:
        return
    src_host = route.get("master_key_from")
    if not src_host:
        return
    key_name = f"master_{instance_id}.key"
    src = f"{src_host}:.coinbot/{key_name}"
    dst = f"{host}:.coinbot/{key_name}"
    subprocess.run(
        ["ssh", src_host, f"test -f ~/.coinbot/{key_name}"],
        capture_output=True,
        timeout=10,
    )
    subprocess.run(["ssh", host, "mkdir -p ~/.coinbot"], capture_output=True, timeout=10)
    subprocess.run(["rsync", "-az", src, dst], capture_output=True, timeout=20)


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
                "host": host,
                "status": "ok" if equity is not None else "unavailable",
                "equity_usd": round(float(equity), 2) if equity is not None else None,
                "assets": assets[:6],
                "error": None if equity is not None else "status cache missing equity",
            }
        ],
    }


def _fetch_status_remote(host: str, instance_id: str) -> dict[str, Any] | None:
    for path in (
        f"/Users/kevinreed/dev/coinbot/coinbot_v2/data/{instance_id}/status.json",
        f"/root/dev/coinbot/coinbot_v2/data/{instance_id}/status.json",
    ):
        proc = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=8", host, f"test -f '{path}' && cat '{path}'"],
            capture_output=True,
            text=True,
            timeout=12,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            try:
                status = json.loads(proc.stdout)
                return _status_to_equity(status, host)
            except json.JSONDecodeError:
                continue
    return None


def _parse_json(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    if not text:
        raise ValueError("empty equity response")
    return json.loads(text)


def _coinbot_python(coinbot_root: Path) -> str:
    for rel in (".venv/bin/python3", "venv/bin/python3"):
        candidate = coinbot_root / rel
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def _runner_env(
    coinbot_root: Path,
    instance_id: str | None,
    market_symbols: str | None,
) -> dict[str, str]:
    env = {**os.environ, "COINBOT_ROOT": str(coinbot_root)}
    if instance_id:
        env["INSTANCE_ID"] = instance_id
    if market_symbols:
        env["MARKET_SYMBOLS"] = market_symbols
        env.setdefault("KRAKEN_LOAD_MARKETS_TIMEOUT_MS", "45000")
    return env


def _runner_cmd(
    py: str,
    runner: Path,
    broker: str,
    force_live: bool,
    timeout_sec: float,
    instance_id: str | None,
    market_symbols: str | None,
) -> list[str]:
    cmd = [py, str(runner), "--brokers", broker, "--timeout", str(timeout_sec)]
    if force_live:
        cmd.append("--force-live")
    if instance_id:
        cmd.extend(["--instance-id", instance_id])
    if market_symbols:
        cmd.extend(["--market-symbols", market_symbols])
    return cmd


def _fetch_local(
    coinbot_root: Path,
    broker: str,
    force_live: bool,
    timeout_sec: float,
    *,
    instance_id: str | None = None,
    market_symbols: str | None = None,
) -> dict[str, Any]:
    runner = SCRIPTS / "equity_remote_runner.py"
    env = _runner_env(coinbot_root, instance_id, market_symbols)
    py = _coinbot_python(coinbot_root)
    cmd = _runner_cmd(py, runner, broker, force_live, timeout_sec, instance_id, market_symbols)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=int(timeout_sec) + 45,
        cwd=coinbot_root,
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


def _remote_modelrouter_dir(host: str, coinbot_root: Path) -> Path:
    if str(coinbot_root).startswith("/root/"):
        return Path("/root/dev/modelrouter")
    return Path(os.environ.get("MODELROUTER_REMOTE_DIR", "/Users/kevinreed/dev/modelrouter"))


def _fetch_remote(
    host: str,
    coinbot_root: Path,
    broker: str,
    force_live: bool,
    timeout_sec: float,
    *,
    instance_id: str | None = None,
    market_symbols: str | None = None,
) -> dict[str, Any]:
    remote_mr = _remote_modelrouter_dir(host, coinbot_root)
    remote_runner = remote_mr / "tokens/scripts/equity_remote_runner.py"
    fallback_runner = Path(str(coinbot_root)) / "equity_remote_runner_mr.py"

    rsync_cmd = [
        "rsync",
        "-az",
        str(SCRIPTS / "equity_remote_runner.py"),
        f"{host}:{remote_runner}",
    ]
    proc_rsync = subprocess.run(rsync_cmd, capture_output=True, text=True, timeout=30)
    runner_path = remote_runner
    if proc_rsync.returncode != 0:
        rsync_cmd[3] = f"{host}:{fallback_runner}"
        subprocess.run(rsync_cmd, capture_output=True, text=True, timeout=30)
        runner_path = fallback_runner

    py_venv = f"{coinbot_root}/.venv/bin/python3"
    py_alt = f"{coinbot_root}/venv/bin/python3"
    inst = instance_id or ""
    markets = market_symbols or ""
    live = " --force-live" if force_live else ""
    inst_arg = f' --instance-id "{inst}"' if inst else ""
    mkt_arg = f' --market-symbols "{markets}"' if markets else ""
    remote_cmd = (
        f"COINBOT_ROOT='{coinbot_root}' "
        f"{f'INSTANCE_ID={inst} ' if inst else ''}"
        f"{f'MARKET_SYMBOLS={markets} ' if markets else ''}"
        f"bash -lc '"
        f"PY=python3; "
        f"test -x \"{py_venv}\" && PY=\"{py_venv}\"; "
        f"test -x \"{py_alt}\" && PY=\"{py_alt}\"; "
        f"exec \"$PY\" \"{runner_path}\" --brokers \"{broker}\" "
        f"--timeout {timeout_sec}{live}{inst_arg}{mkt_arg}'"
    )
    proc = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", host, remote_cmd],
        capture_output=True,
        text=True,
        timeout=int(timeout_sec) + 60,
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

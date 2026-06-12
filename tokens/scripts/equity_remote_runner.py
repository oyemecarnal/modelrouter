#!/usr/bin/env python3
"""Run on kc-mini (Python 3.9+) — JSON equity snapshot via coinbot. No secrets in output."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _coinbot_root() -> Path:
    return Path(os.environ.get("COINBOT_ROOT", Path.home() / "dev" / "coinbot"))


def _setup_path() -> Path:
    root = _coinbot_root()
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


async def _broker_equity(broker: str, force_live: bool, timeout_sec: float) -> dict[str, Any]:
    from loguru import logger

    logger.remove()
    logger.add(sys.stderr, level="ERROR")

    from coinbot_v2.config import load_config
    from coinbot_v2.core.coinbase_adapter import CoinbaseAdapter, _get_coinbase_keys
    from coinbot_v2.core.equity_reader import STABLE_USD_ASSETS, price_asset_usd
    from coinbot_v2.core.kraken import KrakenAdapter

    config = load_config()
    broker = broker.lower().strip()
    quote = getattr(config, "QUOTE_CURRENCY", "USD").upper()
    paper = False if force_live else getattr(config, "TRADING_MODE", "paper").lower() == "paper"

    try:
        if broker == "kraken":
            try:
                api_key = config.get_kraken_api_key()
                api_secret = config.get_kraken_api_secret()
            except Exception as exc:
                return {
                    "broker": broker,
                    "status": "unavailable",
                    "equity_usd": None,
                    "assets": [],
                    "error": f"Kraken credentials: {exc}"[:200],
                }
            if not (api_key and api_secret):
                return {
                    "broker": broker,
                    "status": "unavailable",
                    "equity_usd": None,
                    "assets": [],
                    "error": "Kraken credentials missing or decryption failed",
                }
            exchange = KrakenAdapter(
                api_key=api_key,
                api_secret=api_secret,
                sandbox=getattr(config, "KRAKEN_SANDBOX", False),
                quote_currency=quote,
                paper_mode=paper,
            )
        elif broker == "coinbase":
            api_key, api_secret = _get_coinbase_keys(config)
            if not (api_key and api_secret):
                return {
                    "broker": broker,
                    "status": "unavailable",
                    "equity_usd": None,
                    "assets": [],
                    "error": "Coinbase keys or CDP file missing",
                }
            exchange = CoinbaseAdapter(
                api_key=api_key,
                api_secret=api_secret,
                sandbox=getattr(config, "COINBASE_SANDBOX", False),
                quote_currency=quote,
                paper_mode=paper,
            )
        else:
            return {
                "broker": broker,
                "status": "error",
                "equity_usd": None,
                "assets": [],
                "error": f"Unsupported broker: {broker}",
            }

        await exchange.initialize()
        balances = await exchange.fetch_balances()
        if not balances:
            return {
                "broker": broker,
                "status": "unavailable",
                "equity_usd": None,
                "assets": [],
                "error": "No balances returned",
            }

        rows: list[tuple[str, float]] = []
        for asset, bal in balances.items():
            total = float(getattr(bal, "total", 0.0))
            if total > 0:
                rows.append((asset, total))
        rows.sort(key=lambda r: r[1], reverse=True)

        assets: list[dict[str, Any]] = []
        total_usd = 0.0
        priced = 0
        for asset, amount in rows:
            if asset.upper() in STABLE_USD_ASSETS or asset.upper() == quote:
                price = 1.0
            elif priced >= 6:
                continue
            else:
                try:
                    price, _ = await asyncio.wait_for(
                        price_asset_usd(exchange, asset, quote),
                        timeout=8.0,
                    )
                except Exception:
                    price = 0.0
                priced += 1
            value = amount * price
            total_usd += value
            if value >= 0.01 or asset.upper() in STABLE_USD_ASSETS:
                assets.append(
                    {
                        "asset": asset,
                        "amount": round(amount, 8),
                        "price_usd": round(price, 4),
                        "value_usd": round(value, 2),
                    }
                )
        assets.sort(key=lambda a: a.get("value_usd", 0), reverse=True)

        try:
            await exchange.close()
        except Exception:
            pass

        return {
            "broker": broker,
            "status": "ok",
            "equity_usd": round(total_usd, 2),
            "quote": quote,
            "assets": assets[:8],
            "error": None,
        }
    except Exception as exc:
        return {
            "broker": broker,
            "status": "error",
            "equity_usd": None,
            "assets": [],
            "error": str(exc)[:200],
        }


async def run_all(brokers: list[str], force_live: bool, timeout_sec: float) -> dict[str, Any]:
    rows = []
    for broker in brokers:
        try:
            row = await asyncio.wait_for(
                _broker_equity(broker, force_live, timeout_sec),
                timeout=timeout_sec,
            )
        except asyncio.TimeoutError:
            row = {
                "broker": broker,
                "status": "error",
                "equity_usd": None,
                "assets": [],
                "error": f"timed out after {int(timeout_sec)}s",
            }
        rows.append(row)
    total = sum(r["equity_usd"] or 0 for r in rows if r.get("status") == "ok")
    return {
        "updated_at": int(datetime.now(timezone.utc).timestamp() * 1000),
        "source": "coinbot",
        "host": os.uname().nodename,
        "total_equity_usd": round(total, 2) if total else None,
        "brokers": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="JSON equity snapshot for ModelRouter widget")
    parser.add_argument("--brokers", default="kraken,coinbase", help="Comma-separated brokers")
    parser.add_argument("--force-live", action="store_true", default=True)
    parser.add_argument("--timeout", type=float, default=45.0, help="Per-broker timeout seconds")
    args = parser.parse_args()

    _setup_path()
    brokers = [b.strip() for b in args.brokers.split(",") if b.strip()]
    payload = asyncio.run(run_all(brokers, args.force_live, args.timeout))
    print(json.dumps(payload))
    return 0 if any(b.get("status") == "ok" for b in payload["brokers"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())

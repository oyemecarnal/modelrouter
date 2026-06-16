"""Live Kalshi portfolio balance (cash + positions) for ModelRouter widget."""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def _load_kalshi_settings(dev_root: Path) -> tuple[str, Path, str]:
    """Resolve key id, PEM path, and API base from Kalshi_bot .env."""
    from fetch_usage import resolve_secret

    key_id = resolve_secret("POLYMARKET_KALSHI_API_KEY_ID", dev_root) or resolve_secret("KALSHI_API_KEY_ID", dev_root)
    pem_raw = resolve_secret("POLYMARKET_KALSHI_PRIVATE_KEY_PATH", dev_root) or resolve_secret("KALSHI_PRIVATE_KEY_PATH", dev_root)
    base = (
        resolve_secret("POLYMARKET_KALSHI_BASE_URL", dev_root)
        or resolve_secret("KALSHI_BASE_URL", dev_root)
        or "https://api.elections.kalshi.com/trade-api/v2"
    ).rstrip("/")

    if not key_id or not pem_raw:
        raise RuntimeError("Set POLYMARKET_KALSHI_API_KEY_ID and POLYMARKET_KALSHI_PRIVATE_KEY_PATH in Kalshi_bot/.env")

    pem_path = Path(pem_raw).expanduser()
    if not pem_path.is_absolute():
        for root in (dev_root / "Kalshi_bot", dev_root / "kalshi_bot", Path.home() / "dev" / "Kalshi_bot"):
            candidate = (root / pem_path).resolve()
            if candidate.is_file():
                pem_path = candidate
                break
    if not pem_path.is_file():
        raise RuntimeError(f"Kalshi private key not found: {pem_path}")
    return key_id, pem_path, base


def _sign(private_key: rsa.RSAPrivateKey, text: str) -> str:
    sig = private_key.sign(
        text.encode("utf-8"),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(sig).decode("utf-8")


def _auth_headers(key_id: str, pem_path: Path, method: str, path: str) -> dict[str, str]:
    with pem_path.open("rb") as fh:
        key = serialization.load_pem_private_key(fh.read(), password=None)
    if not isinstance(key, rsa.RSAPrivateKey):
        raise ValueError("Kalshi private key must be RSA PEM")
    ts = str(int(time.time() * 1000))
    clean = path.split("?", 1)[0]
    return {
        "KALSHI-ACCESS-KEY": key_id,
        "KALSHI-ACCESS-TIMESTAMP": ts,
        "KALSHI-ACCESS-SIGNATURE": _sign(key, f"{ts}{method.upper()}{clean}"),
        "Accept": "application/json",
        "User-Agent": "ModelRouter-Keys/1.0",
    }


def _get_json(base: str, key_id: str, pem_path: Path, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    query = f"?{urllib.parse.urlencode(params)}" if params else ""
    url = f"{base}{path}{query}"
    sign_path = f"/trade-api/v2{path}" if not path.startswith("/trade-api") else urlsplit(url).path
    req = urllib.request.Request(url, headers=_auth_headers(key_id, pem_path, "GET", sign_path))
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())
    return data if isinstance(data, dict) else {"data": data}


def _cents_to_usd(value: Any) -> float:
    try:
        return round(float(value) / 100, 2)
    except (TypeError, ValueError):
        return 0.0


def fetch_kalshi_equity(cfg: dict[str, Any]) -> dict[str, Any]:
    dev_root = Path(cfg.get("dev_root") or Path.home() / "dev")
    route = (cfg.get("equity") or {}).get("broker_routes", {}).get("kalshi") or {}
    try:
        key_id, pem_path, base = _load_kalshi_settings(dev_root)
        if route.get("kalshi_base_url"):
            base = str(route["kalshi_base_url"]).rstrip("/")
    except Exception as exc:
        return {
            "broker": "kalshi",
            "type": "prediction",
            "status": "unavailable",
            "equity_usd": None,
            "assets": [],
            "error": str(exc)[:200],
        }

    host = route.get("host") or os.uname().nodename
    try:
        bal = _get_json(base, key_id, pem_path, "/portfolio/balance")
        cash = _cents_to_usd(bal.get("balance"))
        portfolio = _cents_to_usd(bal.get("portfolio_value"))

        positions_payload = _get_json(base, key_id, pem_path, "/portfolio/positions", params={"limit": 200})
        positions = positions_payload.get("market_positions") or []

        assets: list[dict[str, Any]] = []
        if cash > 0:
            assets.append({"asset": "USD cash", "amount": cash, "price_usd": 1.0, "value_usd": cash})
        for pos in positions[:12]:
            exposure = float(pos.get("market_exposure_dollars") or 0)
            ticker = str(pos.get("ticker") or "position")
            qty = float(pos.get("position_fp") or pos.get("position") or 0)
            if exposure <= 0 and qty == 0:
                continue
            assets.append(
                {
                    "asset": ticker,
                    "amount": qty,
                    "price_usd": None,
                    "value_usd": round(exposure, 2),
                }
            )
        assets.sort(key=lambda a: a.get("value_usd") or 0, reverse=True)

        total = round(cash + portfolio, 2)
        return {
            "broker": "kalshi",
            "type": "prediction",
            "host": host,
            "status": "ok",
            "equity_usd": total,
            "cash_usd": cash,
            "portfolio_usd": portfolio,
            "quote": "USD",
            "assets": assets[:10],
            "position_count": len(positions),
            "error": None,
        }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()[:160] if exc.fp else str(exc)
        return {
            "broker": "kalshi",
            "type": "prediction",
            "host": host,
            "status": "error",
            "equity_usd": None,
            "assets": [],
            "error": f"HTTP {exc.code}: {body}",
        }
    except Exception as exc:
        return {
            "broker": "kalshi",
            "type": "prediction",
            "host": host,
            "status": "error",
            "equity_usd": None,
            "assets": [],
            "error": str(exc)[:200],
        }

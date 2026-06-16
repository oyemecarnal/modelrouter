"""Simple USD spot prices for watch-only wallet valuation."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_CACHE: dict[str, Any] = {"at": 0.0, "prices": {}}
TTL_SECONDS = 120
TIMEOUT = 12

SYMBOL_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
}


def _http_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "ModelRouter-Keys/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def spot_usd(symbol: str) -> float | None:
    """Return USD price for a native chain symbol (BTC, ETH, SOL)."""
    sym = (symbol or "").upper()
    if sym in ("USD", "USDC", "USDT", "DAI"):
        return 1.0
    coin_id = SYMBOL_MAP.get(sym)
    if not coin_id:
        return None

    now = time.time()
    if now - float(_CACHE.get("at") or 0) > TTL_SECONDS:
        ids = ",".join(SYMBOL_MAP.values())
        url = f"https://api.coingecko.com/api/v3/simple/price?{urllib.parse.urlencode({'ids': ids, 'vs_currencies': 'usd'})}"
        try:
            data = _http_json(url)
            prices = {k.upper(): v.get("usd") for k, v in ((cid, data.get(cid) or {}) for cid in SYMBOL_MAP.values())}
            rev = {sym: prices.get(cid.upper()) for sym, cid in SYMBOL_MAP.items()}
            _CACHE["prices"] = {k: float(v) for k, v in rev.items() if v is not None}
            _CACHE["at"] = now
        except (urllib.error.URLError, json.JSONDecodeError, TypeError, ValueError):
            pass

    price = (_CACHE.get("prices") or {}).get(sym)
    return float(price) if price is not None else None

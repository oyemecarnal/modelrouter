"""Watch-only on-chain balances and transactions (public address — no custody)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from fetch_usage import resolve_secret
from price_oracle import spot_usd
from wallet_store import get_wallet, list_enabled, load_wallets, mask_address, sync_presets_from_config

TIMEOUT = 15
CACHE_FILE = Path.home() / "Library/Application Support/TokenWidget/wallet_cache.json"


def _http_json(url: str, *, method: str = "GET", body: dict | None = None) -> Any:
    data = None
    headers = {"Accept": "application/json", "User-Agent": "ModelRouter-Keys/1.0"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def _etherscan_key(dev_root: Path | None) -> str | None:
    return resolve_secret("ETHERSCAN_API_KEY", dev_root)


def _cache_ttl(kind: str, cfg: dict[str, Any]) -> int:
    wallets_cfg = cfg.get("wallets") or {}
    if kind == "hot":
        return int(wallets_cfg.get("hot_cache_seconds") or 90)
    return int(wallets_cfg.get("cold_cache_seconds") or 600)


def _read_cache(wallet_id: str, ttl: int) -> dict[str, Any] | None:
    if not CACHE_FILE.exists() or ttl <= 0:
        return None
    try:
        data = json.loads(CACHE_FILE.read_text())
        row = (data.get("balances") or {}).get(wallet_id)
        if not row:
            return None
        age = int(time.time() * 1000) - int(row.get("fetched_at") or 0)
        if age > ttl * 1000:
            return None
        return row
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(wallet_id: str, row: dict[str, Any]) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {"balances": {}}
        if CACHE_FILE.exists():
            data = json.loads(CACHE_FILE.read_text())
        data.setdefault("balances", {})[wallet_id] = row
        CACHE_FILE.write_text(json.dumps(data, indent=2))
    except OSError:
        pass


def fetch_ethereum_balance(address: str, dev_root: Path | None) -> dict[str, Any]:
    api_key = _etherscan_key(dev_root)
    if not api_key:
        return {"status": "unavailable", "error": "Set ETHERSCAN_API_KEY in modelrouter/.env"}
    qs = urllib.parse.urlencode(
        {
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
            "apikey": api_key,
        }
    )
    data = _http_json(f"https://api.etherscan.io/api?{qs}")
    if data.get("status") != "1":
        return {"status": "error", "error": data.get("message") or "Etherscan error"}
    wei = int(data.get("result") or 0)
    eth = wei / 1e18
    return {
        "status": "ok",
        "native_symbol": "ETH",
        "native_amount": round(eth, 8),
        "native_raw": str(wei),
    }


def fetch_ethereum_transactions(address: str, dev_root: Path | None, limit: int = 12) -> list[dict[str, Any]]:
    api_key = _etherscan_key(dev_root)
    if not api_key:
        return []
    qs = urllib.parse.urlencode(
        {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": limit,
            "sort": "desc",
            "apikey": api_key,
        }
    )
    data = _http_json(f"https://api.etherscan.io/api?{qs}")
    if data.get("status") != "1":
        return []
    out = []
    for tx in data.get("result") or []:
        if not isinstance(tx, dict):
            continue
        value_wei = int(tx.get("value") or 0)
        out.append(
            {
                "hash": tx.get("hash"),
                "time": int(tx.get("timeStamp") or 0) * 1000,
                "direction": "in" if tx.get("to", "").lower() == address.lower() else "out",
                "amount": round(value_wei / 1e18, 8),
                "symbol": "ETH",
                "counterparty": tx.get("from") if tx.get("to", "").lower() == address.lower() else tx.get("to"),
            }
        )
    return out


def fetch_bitcoin_balance(address: str) -> dict[str, Any]:
    data = _http_json(f"https://blockstream.info/api/address/{address}")
    chain_stats = data.get("chain_stats") or {}
    funded = int(chain_stats.get("funded_txo_sum") or 0)
    spent = int(chain_stats.get("spent_txo_sum") or 0)
    sats = funded - spent
    return {
        "status": "ok",
        "native_symbol": "BTC",
        "native_amount": round(sats / 1e8, 8),
        "native_raw": str(sats),
    }


def fetch_bitcoin_transactions(address: str, limit: int = 12) -> list[dict[str, Any]]:
    txs = _http_json(f"https://blockstream.info/api/address/{address}/txs")
    out = []
    for tx in (txs or [])[:limit]:
        if not isinstance(tx, dict):
            continue
        txid = tx.get("txid")
        ts = int(tx.get("status", {}).get("block_time") or 0) * 1000
        net = 0
        direction = "in"
        for vout in tx.get("vout") or []:
            if (vout.get("scriptpubkey_address") or "") == address:
                net += int(vout.get("value") or 0)
        for vin in tx.get("vin") or []:
            prev = vin.get("prevout") or {}
            if (prev.get("scriptpubkey_address") or "") == address:
                net -= int(prev.get("value") or 0)
                direction = "out"
        out.append(
            {
                "hash": txid,
                "time": ts,
                "direction": "in" if net >= 0 else "out",
                "amount": round(abs(net) / 1e8, 8),
                "symbol": "BTC",
                "counterparty": None,
            }
        )
    return out


def fetch_solana_balance(address: str) -> dict[str, Any]:
    data = _http_json(
        "https://api.mainnet-beta.solana.com",
        method="POST",
        body={"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [address]},
    )
    lamports = int((data.get("result") or {}).get("value") or 0)
    return {
        "status": "ok",
        "native_symbol": "SOL",
        "native_amount": round(lamports / 1e9, 8),
        "native_raw": str(lamports),
    }


def fetch_solana_transactions(address: str, limit: int = 12) -> list[dict[str, Any]]:
    data = _http_json(
        "https://api.mainnet-beta.solana.com",
        method="POST",
        body={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [address, {"limit": limit}],
        },
    )
    out = []
    for sig in data.get("result") or []:
        if not isinstance(sig, dict):
            continue
        out.append(
            {
                "hash": sig.get("signature"),
                "time": int(sig.get("blockTime") or 0) * 1000,
                "direction": "activity",
                "amount": None,
                "symbol": "SOL",
                "counterparty": None,
                "err": sig.get("err"),
            }
        )
    return out


def fetch_wallet_balance(wallet: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    dev_root = Path(cfg.get("dev_root") or Path.home() / "dev")
    chain = wallet.get("chain", "")
    address = wallet.get("address", "")
    kind = wallet.get("kind", "cold")
    wallet_id = wallet.get("id", "")

    cached = _read_cache(wallet_id, _cache_ttl(kind, cfg))
    if cached:
        cached["cached"] = True
        return cached

    try:
        if chain == "ethereum":
            bal = fetch_ethereum_balance(address, dev_root)
        elif chain == "bitcoin":
            bal = fetch_bitcoin_balance(address)
        elif chain == "solana":
            bal = fetch_solana_balance(address)
        else:
            bal = {"status": "error", "error": f"Unsupported chain: {chain}"}
    except urllib.error.HTTPError as exc:
        bal = {"status": "error", "error": f"HTTP {exc.code}"}
    except Exception as exc:
        bal = {"status": "error", "error": str(exc)[:160]}

    row = {
        "id": wallet_id,
        "label": wallet.get("label"),
        "chain": chain,
        "address_masked": mask_address(address),
        "kind": kind,
        "mode": "live" if kind == "hot" else "last_seen",
        "fetched_at": int(time.time() * 1000),
        **bal,
    }
    sym = bal.get("native_symbol") or ""
    if bal.get("status") == "ok" and bal.get("native_amount") is not None:
        px = spot_usd(sym)
        if px is not None:
            row["price_usd"] = round(px, 2)
            row["value_usd"] = round(float(bal["native_amount"]) * px, 2)
    if bal.get("status") == "ok":
        _write_cache(wallet_id, row)
    return row


def fetch_wallet_transactions(wallet_id: str, cfg: dict[str, Any]) -> dict[str, Any]:
    wallet = get_wallet(wallet_id)
    if not wallet:
        return {"error": "Wallet not found", "transactions": []}

    dev_root = Path(cfg.get("dev_root") or Path.home() / "dev")
    limit = int((cfg.get("wallets") or {}).get("tx_limit") or 12)
    chain = wallet.get("chain", "")
    address = wallet.get("address", "")

    try:
        if chain == "ethereum":
            txs = fetch_ethereum_transactions(address, dev_root, limit)
        elif chain == "bitcoin":
            txs = fetch_bitcoin_transactions(address, limit)
        elif chain == "solana":
            txs = fetch_solana_transactions(address, limit)
        else:
            txs = []
    except Exception as exc:
        return {"wallet_id": wallet_id, "error": str(exc)[:160], "transactions": []}

    for tx in txs:
        if tx.get("counterparty"):
            tx["counterparty_masked"] = mask_address(str(tx["counterparty"]))

    return {
        "wallet_id": wallet_id,
        "label": wallet.get("label"),
        "chain": chain,
        "transactions": txs,
        "fetched_at": int(time.time() * 1000),
    }


def wallet_equity_rows(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """On-chain watch wallets as equity broker rows (Tangem, etc.)."""
    wallets_cfg = cfg.get("wallets") or {}
    if not wallets_cfg.get("enabled", True) or not wallets_cfg.get("include_in_equity", True):
        return []
    sync_presets_from_config(cfg)
    rows = []
    for w in fetch_all_wallets(cfg).get("wallets") or []:
        assets = []
        if w.get("native_amount") is not None:
            assets.append(
                {
                    "asset": w.get("native_symbol") or w.get("chain", "").upper(),
                    "amount": w.get("native_amount"),
                    "price_usd": w.get("price_usd"),
                    "value_usd": w.get("value_usd"),
                }
            )
        rows.append(
            {
                "broker": (w.get("label") or w.get("chain") or "wallet").lower().replace(" ", "-"),
                "display_name": w.get("label") or "Wallet",
                "type": "cold_wallet" if w.get("kind") == "cold" else "hot_wallet",
                "host": "on-chain",
                "status": w.get("status") or "ok",
                "equity_usd": w.get("value_usd"),
                "assets": assets,
                "address_masked": w.get("address_masked"),
                "error": w.get("error"),
            }
        )
    return rows


def fetch_all_wallets(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    from fetch_usage import load_config

    cfg = cfg or load_config()
    wallets_cfg = cfg.get("wallets") or {}
    if not wallets_cfg.get("enabled", True):
        return {"enabled": False, "wallets": []}

    sync_presets_from_config(cfg)
    enabled = list_enabled()
    rows = [fetch_wallet_balance(w, cfg) for w in enabled]
    total_usd = sum(r.get("value_usd") or 0 for r in rows if r.get("status") == "ok")
    return {
        "enabled": True,
        "updated_at": int(time.time() * 1000),
        "wallets": rows,
        "count": len(rows),
        "total_value_usd": round(total_usd, 2) if total_usd else None,
    }

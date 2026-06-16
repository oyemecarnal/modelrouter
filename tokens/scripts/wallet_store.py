"""Persistent watch-only crypto wallets (public addresses only — no private keys)."""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

WALLETS_FILE = Path.home() / "Library/Application Support/TokenWidget/wallets.json"
VERSION = 1

CHAIN_ALIASES = {
    "eth": "ethereum",
    "btc": "bitcoin",
    "sol": "solana",
}

ADDRESS_PATTERNS = {
    "ethereum": re.compile(r"^0x[a-fA-F0-9]{40}$"),
    "bitcoin": re.compile(r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$"),
    "solana": re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$"),
}


def _default_doc() -> dict[str, Any]:
    return {"version": VERSION, "wallets": []}


def load_wallets() -> dict[str, Any]:
    if not WALLETS_FILE.exists():
        return _default_doc()
    try:
        data = json.loads(WALLETS_FILE.read_text())
        if not isinstance(data, dict):
            return _default_doc()
        data.setdefault("version", VERSION)
        data.setdefault("wallets", [])
        return data
    except (json.JSONDecodeError, OSError):
        return _default_doc()


def save_wallets(doc: dict[str, Any]) -> None:
    WALLETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    doc["version"] = VERSION
    tmp = WALLETS_FILE.parent / f".wallets-{uuid.uuid4().hex}.tmp"
    tmp.write_text(json.dumps(doc, indent=2))
    tmp.replace(WALLETS_FILE)


def normalize_chain(chain: str) -> str:
    c = (chain or "").strip().lower()
    return CHAIN_ALIASES.get(c, c)


def validate_address(chain: str, address: str) -> str | None:
    chain = normalize_chain(chain)
    addr = (address or "").strip()
    pat = ADDRESS_PATTERNS.get(chain)
    if not pat:
        return f"Unsupported chain: {chain}"
    if not pat.match(addr):
        return f"Invalid {chain} address"
    return None


def list_enabled(doc: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = doc or load_wallets()
    return [w for w in data.get("wallets", []) if w.get("enabled", True)]


def add_wallet(
    *,
    label: str,
    chain: str,
    address: str,
    kind: str = "cold",
) -> dict[str, Any]:
    chain = normalize_chain(chain)
    err = validate_address(chain, address)
    if err:
        raise ValueError(err)
    kind = (kind or "cold").strip().lower()
    if kind not in ("cold", "hot"):
        raise ValueError("kind must be cold or hot")

    doc = load_wallets()
    address = address.strip()
    for w in doc["wallets"]:
        if w.get("chain") == chain and w.get("address", "").lower() == address.lower():
            raise ValueError("Wallet already tracked")

    entry = {
        "id": uuid.uuid4().hex[:12],
        "label": (label or f"{chain} wallet").strip()[:64],
        "chain": chain,
        "address": address,
        "kind": kind,
        "created_at": int(time.time() * 1000),
        "enabled": True,
    }
    doc["wallets"].append(entry)
    save_wallets(doc)
    return entry


def remove_wallet(wallet_id: str) -> bool:
    doc = load_wallets()
    before = len(doc["wallets"])
    doc["wallets"] = [w for w in doc["wallets"] if w.get("id") != wallet_id]
    if len(doc["wallets"]) == before:
        return False
    save_wallets(doc)
    return True


def get_wallet(wallet_id: str) -> dict[str, Any] | None:
    for w in load_wallets().get("wallets", []):
        if w.get("id") == wallet_id:
            return w
    return None


def sync_presets_from_config(cfg: dict[str, Any]) -> None:
    """Ensure config/env wallet presets exist in the local store (watch-only addresses)."""
    from fetch_usage import resolve_secret

    wallets_cfg = cfg.get("wallets") or {}
    dev_root = Path(cfg.get("dev_root") or Path.home() / "dev")
    presets: list[dict[str, Any]] = list(wallets_cfg.get("presets") or [])

    env_presets = [
        ("Tangem BTC", "bitcoin", resolve_secret("TANGEM_BTC_ADDRESS", dev_root) or resolve_secret("EXTERNAL_WALLET_BTC_ADDRESS", dev_root)),
        ("Tangem ETH", "ethereum", resolve_secret("TANGEM_ETH_ADDRESS", dev_root) or resolve_secret("EXTERNAL_WALLET_ETH_ADDRESS", dev_root)),
        ("Tangem SOL", "solana", resolve_secret("TANGEM_SOL_ADDRESS", dev_root)),
    ]
    for label, chain, address in env_presets:
        if address:
            presets.append({"label": label, "chain": chain, "address": address, "kind": "cold"})

    for preset in presets:
        label = str(preset.get("label") or "Wallet")
        chain = normalize_chain(str(preset.get("chain") or ""))
        address = str(preset.get("address") or "").strip()
        kind = str(preset.get("kind") or "cold")
        if not chain or not address:
            continue
        if validate_address(chain, address):
            continue
        try:
            add_wallet(label=label, chain=chain, address=address, kind=kind)
        except ValueError:
            pass


def mask_address(address: str) -> str:
    if len(address) <= 12:
        return address
    return f"{address[:6]}…{address[-4:]}"

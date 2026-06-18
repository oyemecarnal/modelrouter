"""Shared homelab host config — merges hosts.yaml + optional hosts.local.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def load_hosts(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    try:
        import yaml

        data: dict[str, Any] = {}
        base = root / "config" / "hosts.yaml"
        local = root / "config" / "hosts.local.yaml"
        if base.is_file():
            data = yaml.safe_load(base.read_text()) or {}
        if local.is_file():
            overlay = yaml.safe_load(local.read_text()) or {}
            for key, val in overlay.items():
                if isinstance(val, dict) and isinstance(data.get(key), dict):
                    data[key] = {**data[key], **val}
                else:
                    data[key] = val
        return data
    except Exception:
        return {}


def gateway_ssh_host(root: Path | None = None) -> str:
    if os.environ.get("MODELROUTER_REMOTE_HOST"):
        return os.environ["MODELROUTER_REMOTE_HOST"]
    hosts = (load_hosts(root).get("hosts") or {}).get("gateway-mini") or {}
    return str(hosts.get("ssh") or "gateway-mini")


def gateway_url(root: Path | None = None, *, field: str = "url") -> str:
    gw = load_hosts(root).get("gateway") or {}
    port = os.environ.get("MODELROUTER_PORT", "3000")
    return str(gw.get(field) or gw.get("url_local") or f"http://gateway.local:{port}")

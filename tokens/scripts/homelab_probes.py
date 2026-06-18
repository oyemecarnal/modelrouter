"""Shared homelab connectivity probes — used by widget and ops scripts."""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def load_hosts(root: Path) -> dict[str, Any]:
    try:
        import yaml

        base_path = root / "config" / "hosts.yaml"
        local_path = root / "config" / "hosts.local.yaml"
        data: dict[str, Any] = {}
        if base_path.exists():
            data = yaml.safe_load(base_path.read_text()) or {}
        if local_path.exists():
            overlay = yaml.safe_load(local_path.read_text()) or {}
            for key, val in overlay.items():
                if isinstance(val, dict) and isinstance(data.get(key), dict):
                    data[key] = {**data[key], **val}
                else:
                    data[key] = val
        return data
    except Exception:
        pass
    return {}


def parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip("'\"").strip()
    return out


def probe_url(url: str, timeout: float = 3.0) -> bool:
    try:
        req = urllib.request.Request(f"{url.rstrip('/')}/health/liveliness")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False


def probe_http(url: str, timeout: float = 3.0) -> bool:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 500
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False


def probe_models(base: str, key: str, timeout: float = 4.0) -> bool:
    if not key:
        return False
    try:
        req = urllib.request.Request(
            f"{base.rstrip('/')}/v1/models",
            headers={"Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            ids = {m.get("id") for m in data.get("data", []) if m.get("id")}
            return bool({"cheap", "hermes-fast", "smart"} & ids)
    except Exception:
        return False


def ssh_ok(host: str, timeout: int = 3) -> bool:
    try:
        proc = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=3", "-o", "BatchMode=yes", host, "true"],
            capture_output=True,
            timeout=timeout,
        )
        return proc.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def tower_to_mini(host: str, gw_url: str, timeout: int = 6) -> bool:
    try:
        proc = subprocess.run(
            [
                "ssh",
                "-o",
                "ConnectTimeout=4",
                "-o",
                "BatchMode=yes",
                host,
                f"curl -sf --max-time 4 {gw_url.rstrip('/')}/health/liveliness",
            ],
            capture_output=True,
            timeout=timeout,
        )
        return proc.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False

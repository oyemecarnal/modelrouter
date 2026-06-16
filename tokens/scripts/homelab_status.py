"""Homelab path probes for widget receiver LED bar — masked, no secrets in output."""

from __future__ import annotations

import socket
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from receiver_themes import merge_custom, presets_for_snapshot


def _modelrouter_root(cfg: dict[str, Any]) -> Path:
    return Path(cfg.get("modelrouter_root") or Path.home() / "dev" / "modelrouter")


def _load_hosts(root: Path) -> dict[str, Any]:
    try:
        import yaml

        path = root / "config" / "hosts.yaml"
        if path.exists():
            return yaml.safe_load(path.read_text()) or {}
    except Exception:
        pass
    return {}


def _parse_env(path: Path) -> dict[str, str]:
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


def _probe_url(url: str, timeout: float = 3.0) -> bool:
    try:
        req = urllib.request.Request(f"{url.rstrip('/')}/health/liveliness")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False


def _probe_http(url: str, timeout: float = 3.0) -> bool:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 500
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False


def _probe_models(base: str, key: str, timeout: float = 4.0) -> bool:
    if not key:
        return False
    try:
        req = urllib.request.Request(
            f"{base.rstrip('/')}/v1/models",
            headers={"Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            import json

            data = json.loads(resp.read().decode())
            ids = {m.get("id") for m in data.get("data", []) if m.get("id")}
            return bool({"cheap", "hermes-fast", "smart"} & ids)
    except Exception:
        return False


def _ssh_ok(host: str, timeout: int = 3) -> bool:
    try:
        proc = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=3", "-o BatchMode=yes", host, "true"],
            capture_output=True,
            timeout=timeout,
        )
        return proc.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def _tower_to_mini(host: str, gw_url: str, timeout: int = 6) -> bool:
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


def _led(led_id: str, label: str, state: str, detail: str = "", kind: str = "") -> dict[str, str]:
    row: dict[str, str] = {"id": led_id, "label": label, "state": state, "detail": detail}
    if kind:
        row["kind"] = kind
    return row


def _key_state(env_var: str, value: str, validators: dict[str, str]) -> str:
    val = (value or "").strip()
    if not val or val.startswith("op://"):
        return "down" if not val else "warn"
    prefix = validators.get(env_var)
    if prefix and not val.startswith(prefix):
        return "warn"
    return "ok"


_PREFIX_HINTS: dict[str, str] = {
    "GROQ_API_KEY": "gsk_",
    "ANTHROPIC_API_KEY": "sk-ant-",
    "OPENAI_API_KEY": "sk-",
    "MISTRAL_API_KEY": "",
    "GOOGLE_API_KEY": "AIza",
    "DEEPSEEK_API_KEY": "sk-",
    "TOGETHER_API_KEY": "",
    "FIREWORKS_API_KEY": "fw_",
}

# Non-registry keys shown on receiver bar (laptop / stub providers)
EXTRA_CONNECTOR_DEFS: list[dict[str, str]] = [
    {"id": "cursor", "label": "CURSOR", "env": "CURSOR_API_KEY", "prefix": ""},
    {"id": "openrouter", "label": "OROUTE", "env": "OPENROUTER_API_KEY", "prefix": "sk-or-"},
]


def _load_registry_connectors(root: Path) -> list[dict[str, str]]:
    """Paste-key connectors from config/connectors.yaml (SSOT)."""
    try:
        import yaml

        path = root / "config" / "connectors.yaml"
        if not path.exists():
            return []
        reg = yaml.safe_load(path.read_text()) or {}
        out: list[dict[str, str]] = []
        for cid, c in (reg.get("connectors") or {}).items():
            env_var = (c or {}).get("env") or ""
            label = ((c or {}).get("label") or cid).upper()[:6]
            prefix = _PREFIX_HINTS.get(env_var, "")
            out.append(
                {
                    "id": cid,
                    "label": label,
                    "env": env_var,
                    "prefix": prefix,
                    "signup": (c or {}).get("signup") or "",
                    "make": (c or {}).get("make_target") or f"connect-{cid}",
                }
            )
        return out
    except Exception:
        return []


DEFAULT_WEBHOOKS = [
    {"id": "groq_net", "label": "GROQ", "url": "https://api.groq.com"},
    {"id": "openai_net", "label": "OAI", "url": "https://api.openai.com/v1/models"},
    {"id": "anthropic_net", "label": "ANTH", "url": "https://api.anthropic.com"},
    {"id": "mini_gw", "label": "MINI", "url": "http://Kevins-Mac-mini.local:3000/health/liveliness"},
]


def load_homelab_status(cfg: dict[str, Any]) -> dict[str, Any]:
    """Probe paths, API keys, and webhook reachability for receiver LEDs."""
    rx = cfg.get("receiver") or {}
    if not rx.get("enabled", True):
        return {"enabled": False, "themePresets": presets_for_snapshot(cfg), "rows": [], "leds": []}

    root = _modelrouter_root(cfg)
    hosts = _load_hosts(root)
    gw = hosts.get("gateway") or {}
    env = _parse_env(root / ".env")
    port = env.get("MODELROUTER_PORT", "3000")
    local_url = gw.get("url_local") or f"http://127.0.0.1:{port}"
    mini_urls = [
        gw.get("url"),
        gw.get("url_tailscale"),
        f"http://Kevins-Mac-mini.local:{port}",
        f"http://100.85.245.23:{port}",
    ]
    mini_urls = [u for u in mini_urls if u]

    master = env.get("MODELROUTER_MASTER_KEY", "")
    salt = env.get("LITELLM_SALT_KEY", "")

    preset_id = rx.get("default_preset") or "classic-rg"
    theme = merge_custom(preset_id, rx)
    theme_meta = presets_for_snapshot(cfg)

    infra: list[dict[str, str]] = []
    laptop_up = _probe_url(local_url)
    laptop_detail = "Local gateway" if laptop_up else "down — make ensure-gateway"
    infra.append(
        _led("laptop", "LAPTOP", "ok" if laptop_up else "down", laptop_detail, "path")
    )

    mini_up = False
    mini_hit = ""
    for url in mini_urls:
        if _probe_url(url):
            mini_up = True
            mini_hit = url
            break
    infra.append(_led("mini", "MINI", "ok" if mini_up else "down", mini_hit or "kc-mini", "path"))

    tower_host = None
    for candidate in ("kc-tower", "kc-tower-lan"):
        if _ssh_ok(candidate):
            tower_host = candidate
            break
    infra.append(
        _led("tower", "TWR", "ok" if tower_host else "skip", tower_host or "offline", "path")
    )

    tailscale_gw = gw.get("url_tailscale") or f"http://100.85.245.23:{port}"
    if tower_host:
        link_ok = _tower_to_mini(tower_host, tailscale_gw)
        infra.append(
            _led("link", "LINK", "ok" if link_ok else "warn", "tower→mini", "path")
        )
    else:
        infra.append(_led("link", "LINK", "skip", "tower offline", "path"))

    master_ok = bool(master) and "change-me" not in master and "local-dev" not in master
    infra.append(_led("mrkey", "MRKEY", "ok" if master_ok else "warn", "master key", "path"))

    salt_ok = bool(salt) and salt != master
    infra.append(_led("salt", "SALT", "ok" if salt_ok else "warn", "distinct salt", "path"))

    cursor_ok = laptop_up and _probe_models(local_url, master)
    infra.append(
        _led(
            "cursor",
            "CURSOR",
            "ok" if cursor_ok else ("warn" if laptop_up else "down"),
            "/v1 models",
            "path",
        )
    )

    connector_defs = _load_registry_connectors(root) + EXTRA_CONNECTOR_DEFS

    validators = {c["env"]: c["prefix"] for c in connector_defs}
    connectors: list[dict[str, str]] = []
    for conn in connector_defs:
        cid = conn["id"]
        label = conn["label"]
        env_var = conn["env"]
        val = env.get(env_var, "")
        if env_var == "GOOGLE_API_KEY" and not val:
            val = env.get("GEMINI_API_KEY", "")
        state = _key_state(env_var, val, validators)
        if env_var == "OPENROUTER_API_KEY" and state == "ok":
            state = "warn"
            detail = "stubbed — not routed"
        else:
            detail = "configured" if state == "ok" else "missing"
        led = _led(cid, label, state, detail, "api")
        if conn.get("signup"):
            led["signup"] = conn["signup"]
        connectors.append(led)

    webhooks_cfg = rx.get("webhooks") or DEFAULT_WEBHOOKS
    webhooks: list[dict[str, str]] = []
    for wh in webhooks_cfg:
        if not isinstance(wh, dict):
            continue
        url = wh.get("url") or ""
        label = wh.get("label") or wh.get("id") or "WH"
        wid = wh.get("id") or label.lower()
        if not url:
            continue
        up = _probe_http(url)
        webhooks.append(_led(wid, label[:6], "ok" if up else "down", url, "webhook"))

    rows = [
        {"id": "infra", "label": "PATHS", "leds": infra},
        {"id": "connectors", "label": "API KEYS", "leds": connectors},
        {"id": "webhooks", "label": "NETWORK", "leds": webhooks},
    ]
    flat = infra + connectors + webhooks

    led_by_id = {l["id"]: l for l in connectors}
    registry_connectors: list[dict[str, str]] = []
    for conn in _load_registry_connectors(root):
        led = led_by_id.get(conn["id"], {})
        registry_connectors.append(
            {
                "id": conn["id"],
                "label": conn["label"],
                "env": conn.get("env") or "",
                "prefix": conn.get("prefix") or "",
                "signup": conn.get("signup") or "",
                "make": f"make {conn.get('make') or 'connect-' + conn['id']}",
                "state": led.get("state") or "down",
            }
        )

    hints: list[dict[str, str]] = []
    if not laptop_up:
        hints.append(
            {
                "id": "laptop_gateway",
                "text": "Laptop gateway down — Cursor may bypass ModelRouter",
                "fix": "make ensure-gateway",
                "alt": "make daemon-enable",
                "doc": "docs/LAPTOP_DAEMON.md",
            }
        )
    if not mini_up:
        hints.append(
            {
                "id": "mini_gateway",
                "text": "kc-mini gateway unreachable",
                "fix": "ssh kc-mini-lan 'cd ~/dev/modelrouter && make restart'",
                "alt": "",
                "doc": "docs/HOMELAB_GOALS.md",
            }
        )

    vault_path = root / "data" / "key_vault.json"
    if not vault_path.is_file():
        hints.append(
            {
                "id": "key_vault",
                "text": "Network key vault empty — keys may be scattered",
                "fix": "make vault-scrape-collect",
                "alt": "make vault-export",
                "doc": "docs/KEY_VAULT.md",
            }
        )

    return {
        "enabled": True,
        "host": socket.gethostname(),
        "defaultPreset": theme_meta["defaultPreset"],
        "themePresets": theme_meta["presets"],
        "theme": theme,
        "rows": rows,
        "leds": flat,
        "registryConnectors": registry_connectors,
        "hints": hints,
    }

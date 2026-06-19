"""Homelab path probes for widget receiver LED bar — masked, no secrets in output."""

from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

from homelab_probes import (
    load_hosts as _load_hosts,
    parse_env as _parse_env,
    probe_http as _probe_http,
    probe_models as _probe_models,
    probe_url as _probe_url,
    ssh_ok as _ssh_ok,
    tower_to_mini as _tower_to_mini,
)
from receiver_themes import merge_custom, presets_for_snapshot


def _modelrouter_root(cfg: dict[str, Any]) -> Path:
    return Path(cfg.get("modelrouter_root") or Path.home() / "dev" / "modelrouter")


def _last_rotate_hint(root: Path) -> dict[str, Any] | None:
    path = root / "data" / "key_rotate_hints.json"
    if not path.is_file():
        return None
    try:
        rows = json.loads(path.read_text())
        if not isinstance(rows, list):
            return None
        return next((h for h in reversed(rows) if h.get("ok") and not h.get("applied_at")), None)
    except (json.JSONDecodeError, OSError):
        return None


def _vault_alt_readiness(root: Path) -> dict[str, Any]:
    try:
        import sys

        rstr = str(root)
        if rstr not in sys.path:
            sys.path.insert(0, rstr)
        from modelrouter.key_vault import vault_alt_readiness

        return vault_alt_readiness()
    except Exception:
        return {"ready": {}, "missing": [], "shuffle_ready": False, "counts": {}}



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
]


def _gateway_webhook(root: Path, port: str) -> dict[str, str]:
    hosts = _load_hosts(root)
    gw = hosts.get("gateway") or {}
    base = (gw.get("url") or gw.get("url_local") or f"http://gateway.local:{port}").rstrip("/")
    return {"id": "mini_gw", "label": "GW", "url": f"{base}/health/liveliness"}


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
    mini_urls = [u for u in (gw.get("url"), gw.get("url_tailscale"), gw.get("url_ssh_alias")) if u]

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
    infra.append(_led("mini", "MINI", "ok" if mini_up else "down", mini_hit or "gateway", "path"))

    tower_host = None
    for candidate in ("gateway-tower", "kc-tower", "kc-tower-lan"):
        if _ssh_ok(candidate):
            tower_host = candidate
            break
    infra.append(
        _led("tower", "TWR", "ok" if tower_host else "skip", tower_host or "offline", "path")
    )

    # LINK = can this laptop reach the tower gateway? Only uses explicitly configured url_tower.
    tower_url = gw.get("url_tower")
    if tower_url:
        link_ok = _probe_url(tower_url)
        infra.append(
            _led("link", "LINK", "ok" if link_ok else "warn", f"laptop→tower ({tower_url})", "path")
        )
    else:
        infra.append(_led("link", "LINK", "skip", "set url_tower in hosts config", "path"))

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

    rotate_hint = _last_rotate_hint(root)
    if rotate_hint:
        fp = str(rotate_hint.get("next_fingerprint") or "?")[:12]
        infra.append(
            _led(
                "rotate",
                "ROTATE",
                "warn",
                f"{rotate_hint.get('env_var', '?')} → {fp}",
                "path",
            )
        )

    alt_ready = _vault_alt_readiness(root)
    n_ready = sum(1 for v in alt_ready.get("ready", {}).values() if v)
    n_total = len(alt_ready.get("ready") or {})
    if n_total:
        if n_ready < n_total:
            infra.append(
                _led(
                    "alts",
                    "ALTS",
                    "warn",
                    f"{n_ready}/{n_total} shuffle",
                    "path",
                )
            )
        else:
            infra.append(
                _led("alts", "ALTS", "ok", f"{n_total} shuffle-ready", "path")
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

    webhooks_cfg = rx.get("webhooks") or (DEFAULT_WEBHOOKS + [_gateway_webhook(root, port)])
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
                "fix": "make doctor-fix",
                "alt": "make daemon-enable",
                "doc": "docs/LAPTOP_DAEMON.md",
            }
        )
    if not mini_up:
        hints.append(
            {
                "id": "mini_gateway",
                "text": "kc-mini gateway unreachable",
                "fix": "ssh $MODELROUTER_REMOTE_HOST 'cd ~/dev/modelrouter && make restart'",
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

    if rotate_hint:
        hints.append(
            {
                "id": "key_rotate",
                "text": f"429 rotate pending — {rotate_hint.get('env_var', 'key')}",
                "fix": "make vault-rotate-push",
                "alt": "make vault-rotate-export",
                "doc": "docs/KEY_VAULT.md",
            }
        )

    alt_missing = alt_ready.get("missing") or []
    if alt_missing:
        n_ready = sum(1 for v in alt_ready.get("ready", {}).values() if v)
        n_total = len(alt_ready.get("ready") or {})
        partial = n_ready > 0 and n_ready < n_total
        hints.append(
            {
                "id": "alt_keys",
                "text": (
                    f"Alt shuffle partial ({n_ready}/{n_total}) — still need: {', '.join(alt_missing)}"
                    if partial
                    else f"Alt shuffle inactive — need 2+ keys: {', '.join(alt_missing)}"
                ),
                "fix": "make connect-alt-key PROVIDER=mistral",
                "alt": "make vault-bootstrap-alts",
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

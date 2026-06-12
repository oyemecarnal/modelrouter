"""
Generate data/CORE_APIS.md — private live API inventory (gitignored).

Never writes full secret values. Regenerate: make core-apis
"""

from __future__ import annotations

import re
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "CORE_APIS.md"
CATALOG = ROOT / "config" / "api_catalog.yaml"
MODELS = ROOT / "config" / "models_catalog.yaml"
PROJECTS = ROOT / "config" / "projects.yaml"
ENV_FILE = ROOT / ".env"
INVENTORY_SNAPSHOT = ROOT / "data" / "inventory_snapshot.json"

PLACEHOLDER_RE = re.compile(r"change-me|local-dev|placeholder", re.I)
OP_REF = re.compile(r"^op://")

# Provider keys actively routed in config/modelrouter*.yaml (native homelab).
GATEWAY_WIRED = {
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "MISTRAL_API_KEY",
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
}
GATEWAY_STUB = {"OPENROUTER_API_KEY"}
GATEWAY_NEEDS_KEY = {"ANTHROPIC_API_KEY"}
CLIENT_ONLY = {
    "CURSOR_API_KEY",
    "MODELROUTER_MASTER_KEY",
    "LITELLM_SALT_KEY",
    "MODELROUTER_KEY_HERMES",
    "MODELROUTER_KEY_KALSHI",
    "MODELROUTER_KEY_COINBOT",
    "MODELROUTER_KEY_CURSOR",
    "MODELROUTER_KEY_AGENTS",
}


def mask_value(value: str) -> str:
    value = value.strip().strip("'\"")
    if not value:
        return ""
    if OP_REF.match(value):
        return value
    if value.startswith("/") or value.endswith(".json"):
        return value if len(value) < 80 else f"{value[:40]}…"
    if len(value) <= 8:
        return "••••••••"
    return f"{value[:4]}…{value[-4:]}"


def parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def key_state(env: str, laptop: dict[str, str], mini: set[str]) -> dict[str, Any]:
    val = laptop.get(env, "")
    on_laptop = bool(val)
    on_mini = env in mini
    if not on_laptop and not on_mini:
        status = "missing"
    elif val and PLACEHOLDER_RE.search(val):
        status = "placeholder"
    elif on_laptop or on_mini:
        status = "configured"
    else:
        status = "missing"

    routing = "not_llm"
    if env in GATEWAY_WIRED:
        routing = "gateway_wired"
    elif env in GATEWAY_STUB:
        routing = "gateway_stub"
    elif env in GATEWAY_NEEDS_KEY:
        routing = "gateway_wired_key_empty" if status != "configured" else "gateway_wired"
    elif env in CLIENT_ONLY or env.startswith("MODELROUTER_"):
        routing = "client_or_gateway_auth"
    elif env.endswith("_API_KEY") or env.endswith("_TOKEN") or env.endswith("_SECRET"):
        routing = "app_direct"

    return {
        "status": status,
        "laptop": on_laptop,
        "mini": on_mini,
        "masked": mask_value(val) if on_laptop else None,
        "routing": routing,
    }


def mini_env_keys() -> set[str]:
    try:
        proc = subprocess.run(
            [
                "ssh",
                "-o",
                "ConnectTimeout=4",
                "-o",
                "BatchMode=yes",
                "kc-mini-lan",
                "grep -E '^[A-Z][A-Z0-9_]*=' ~/dev/modelrouter/.env 2>/dev/null | cut -d= -f1",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if proc.returncode != 0:
            return set()
        return {ln.strip() for ln in proc.stdout.splitlines() if ln.strip()}
    except (subprocess.TimeoutExpired, OSError):
        return set()


def json_load(path: Path) -> dict[str, Any]:
    import json

    return json.loads(path.read_text())


def routing_label(code: str) -> str:
    return {
        "gateway_wired": "LiteLLM gateway (active)",
        "gateway_stub": "OpenRouter stub (not routed)",
        "gateway_wired_key_empty": "Gateway config — **key empty**",
        "client_or_gateway_auth": "Client auth / not provider",
        "app_direct": "App / data API (bypass gateway)",
        "not_llm": "—",
    }.get(code, code)


def status_icon(status: str) -> str:
    return {
        "configured": "✅",
        "placeholder": "⚠️",
        "missing": "❌",
    }.get(status, "?")


def build_markdown() -> str:
    laptop = parse_env(ENV_FILE)
    mini = mini_env_keys()
    cat = yaml.safe_load(CATALOG.read_text()) if CATALOG.exists() else {}
    models = yaml.safe_load(MODELS.read_text()) if MODELS.exists() else {}
    projects = yaml.safe_load(PROJECTS.read_text()) if PROJECTS.exists() else {}

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    host = socket.gethostname()

    lines: list[str] = [
        "# Core API list (private)",
        "",
        f"> **Generated:** {now} · **Host:** {host} · **Regenerate:** `make core-apis`",
        "",
        "**Never commit this file.** Values are masked. Full secrets stay in `.env` / kc-mini only.",
        "",
        "## Summary",
        "",
    ]

    families = cat.get("families") or []
    total_keys = 0
    configured = 0
    gateway_active = 0
    for fam in families:
        for kd in fam.get("keys") or []:
            if kd.get("hidden"):
                continue
            env = kd.get("env", "")
            if not env:
                continue
            total_keys += 1
            st = key_state(env, laptop, mini)
            if st["status"] == "configured":
                configured += 1
            if st["routing"] == "gateway_wired":
                gateway_active += 1

    lines.extend(
        [
            f"- **Catalog keys tracked:** {total_keys}",
            f"- **Configured (laptop and/or mini):** {configured}",
            f"- **Gateway-routed providers:** {gateway_active}",
            f"- **ModelRouter master:** `{'set' if laptop.get('MODELROUTER_MASTER_KEY') else 'missing'}` "
            f"(Cursor-compatible `crsr_*` — do not rotate without updating Cursor)",
            f"- **Mini SSH key names:** {len(mini)} vars in `~/dev/modelrouter/.env`",
            "",
            "## Gateway presets (models_catalog)",
            "",
            "| Preset | Tier | Max tokens | Clients |",
            "|--------|------|------------|---------|",
        ]
    )
    for pname, pinfo in sorted((models.get("presets") or {}).items()):
        if not isinstance(pinfo, dict):
            continue
        clients = ", ".join(pinfo.get("clients") or []) or "—"
        lines.append(
            f"| `{pname}` | {pinfo.get('cost_tier', '—')} | "
            f"{pinfo.get('max_tokens_default', '—')} | {clients} |"
        )

    lines.extend(["", "## Projects → presets", "", "| Project | Hosts | Presets | Virtual key |", "|---------|-------|---------|-------------|"])
    for pid, p in (projects.get("projects") or {}).items():
        presets = p.get("presets") or {}
        ps = ", ".join(f"{k}={v}" for k, v in presets.items())
        lines.append(
            f"| {pid} | {', '.join(p.get('hosts') or [])} | {ps} | `{p.get('virtual_key_env', '—')}` |"
        )

    lines.extend(["", "## API families", ""])

    for fam in families:
        fid = fam.get("id", "")
        label = fam.get("label", fid)
        purpose = fam.get("purpose", "")
        fit = ", ".join(fam.get("repo_fit") or []) or "—"
        lines.append(f"### {label} (`{fid}`)")
        lines.append("")
        lines.append(f"*{purpose}* · repo_fit: {fit}")
        lines.append("")
        lines.append("| Env | Status | Laptop | Mini | Routing | Masked | Signup |")
        lines.append("|-----|--------|--------|------|---------|--------|--------|")

        for kd in fam.get("keys") or []:
            if kd.get("hidden"):
                continue
            env = kd.get("env", "")
            st = key_state(env, laptop, mini)
            signup = kd.get("signup", "")
            signup_cell = f"[link]({signup})" if signup else "—"
            lines.append(
                f"| `{env}` | {status_icon(st['status'])} {st['status']} | "
                f"{'✓' if st['laptop'] else '—'} | {'✓' if st['mini'] else '—'} | "
                f"{routing_label(st['routing'])} | {st['masked'] or '—'} | {signup_cell} |"
            )
        lines.append("")

    if INVENTORY_SNAPSHOT.exists():
        lines.extend(["## Disk locations (inventory snapshot)", ""])
        try:
            data = json_load(INVENTORY_SNAPSHOT)
            by_name: dict[str, list[str]] = {}
            for item in data.get("api") or []:
                name = item.get("name")
                path = item.get("path")
                if name and path:
                    by_name.setdefault(name, []).append(path)
            for name in sorted(by_name.keys())[:40]:
                paths = sorted(set(by_name[name]))[:3]
                lines.append(f"- `{name}`: " + ", ".join(f"`{p}`" for p in paths))
        except Exception:
            lines.append("- (snapshot unreadable)")
        lines.append("")

    lines.extend(
        [
            "## Human actions",
            "",
            "- [ ] Confirm Cursor → ModelRouter URL + master key",
            "- [ ] Add `ANTHROPIC_API_KEY` on mini for `hermes-smart` / `review`",
            "- [ ] Rotate Groq key (prior exposure)",
            "- [ ] `make push-client-env-tower` when kc-tower is online",
            "- [ ] Run `make inventory` monthly; `make core-apis` after key changes",
            "",
            "## Commands",
            "",
            "```bash",
            "make core-apis      # regenerate this file",
            "make keys-audit     # masked discover-keys",
            "make inventory      # machine scan → data/inventory_snapshot.json",
            "make push-env-mini  # sync laptop .env keys to kc-mini",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_markdown())
    print(f"[core-apis] Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

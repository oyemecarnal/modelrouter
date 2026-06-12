"""Scan ~/dev and modelrouter for API keys — masked, one card per key."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fetch_usage import (
    AI_KEY_PATTERN,
    ProviderSnapshot,
    UsageWindow,
    parse_env_file,
    resolve_secret,
)

KEY_LABELS: dict[str, str] = {
    "OPENAI_API_KEY": "OpenAI",
    "ANTHROPIC_API_KEY": "Anthropic",
    "GOOGLE_API_KEY": "Google AI",
    "GEMINI_API_KEY": "Gemini",
    "OPENROUTER_API_KEY": "OpenRouter",
    "GROQ_API_KEY": "Groq",
    "MISTRAL_API_KEY": "Mistral",
    "CURSOR_API_KEY": "Cursor API",
    "MODELROUTER_MASTER_KEY": "ModelRouter",
    "LITELLM_SALT_KEY": "LiteLLM Salt",
    "COHERE_API_KEY": "Cohere",
    "DEEPSEEK_API_KEY": "DeepSeek",
    "TOGETHER_API_KEY": "Together AI",
    "FIREWORKS_API_KEY": "Fireworks",
    "XAI_API_KEY": "xAI",
    "PERPLEXITY_API_KEY": "Perplexity",
    "HUGGINGFACE_API_KEY": "Hugging Face",
    "POLYGON_API_KEY": "Polygon",
    "TELEGRAM_BOT_TOKEN": "Telegram",
    "GITHUB_TOKEN": "GitHub",
    "GH_TOKEN": "GitHub",
}

OP_REF = re.compile(r"^op://")


def mask_value(value: str) -> str:
    if OP_REF.match(value):
        return value
    if len(value) <= 8:
        return "••••••••"
    return f"{value[:4]}…{value[-4:]}"


def _scan_env_file(path: Path, dev_root: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if val and AI_KEY_PATTERN.match(f"{key}="):
                try:
                    rel = str(path.relative_to(dev_root))
                except ValueError:
                    rel = str(path)
                found[key] = rel
    except OSError:
        pass
    return found


def _scan_yaml_secrets(path: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    if not path.exists():
        return found
    try:
        in_secrets = False
        for line in path.read_text().splitlines():
            s = line.strip()
            if s == "secrets:":
                in_secrets = True
                continue
            if not in_secrets or not s or s.startswith("#"):
                continue
            if s.endswith(":") and not s.startswith(" "):
                in_secrets = False
                continue
            if ":" not in s:
                continue
            key, val = s.split(":", 1)
            key = key.strip()
            val = val.strip()
            if key and val and OP_REF.match(val):
                found[key] = f"1Password ({val})"
    except OSError:
        pass
    return found


def collect_key_sources(cfg: dict[str, Any]) -> dict[str, str]:
    """key_name -> human source label (best / first wins for display)."""
    dev_root = Path(cfg.get("dev_root") or Path.home() / "dev")
    modelrouter_root = Path(cfg.get("modelrouter_root") or dev_root / "modelrouter")
    sources: dict[str, str] = {}

    extra = [modelrouter_root / ".env", modelrouter_root / "secrets.yaml"]
    for p in extra:
        if p.suffix == ".yaml":
            for k, src in _scan_yaml_secrets(p).items():
                sources.setdefault(k, src)
        elif p.exists():
            for k, rel in _scan_env_file(p, dev_root).items():
                sources.setdefault(k, rel)

    if dev_root.is_dir():
        env_files = set(dev_root.glob("**/.env"))
        env_files.update(dev_root.glob("**/.env.*"))
        for env_path in sorted(env_files):
            if env_path.name.endswith((".example", ".template", ".bak", ".backup")):
                continue
            if "node_modules" in env_path.parts or ".venv" in env_path.parts:
                continue
            for k, rel in _scan_env_file(env_path, dev_root).items():
                sources.setdefault(k, rel)

    zshrc = Path.home() / ".zshrc"
    if zshrc.exists():
        for k, _ in _scan_env_file(zshrc, dev_root).items():
            sources.setdefault(k, "~/.zshrc")

    return sources


PRIORITY_KEYS = frozenset(
    {
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "OPENROUTER_API_KEY",
        "GROQ_API_KEY",
        "MISTRAL_API_KEY",
        "CURSOR_API_KEY",
        "MODELROUTER_MASTER_KEY",
        "POLYGON_API_KEY",
        "GITHUB_TOKEN",
    }
)


def discover_key_cards(cfg: dict[str, Any]) -> list[ProviderSnapshot]:
    dev_root = Path(cfg.get("dev_root") or Path.home() / "dev")
    sources = collect_key_sources(cfg)
    cards: list[ProviderSnapshot] = []

    for key_name in sorted(set(sources) | PRIORITY_KEYS):
        label = KEY_LABELS.get(key_name, key_name.replace("_", " ").title())
        source = sources.get(key_name, "")
        value = resolve_secret(key_name, dev_root)

        if value:
            status = "ok"
            detail = mask_value(value)
        elif source and "1Password" in source:
            status = "configured"
            detail = source
        elif source:
            status = "configured"
            detail = f"set in {source}"
        else:
            status = "unavailable"
            detail = "not found"

        slug = key_name.lower().replace("_", "-")
        cards.append(
            ProviderSnapshot(
                id=f"key-{slug}",
                name=label,
                status=status,
                kind="configured",
                plan=source.split(":")[0] if source else None,
                windows=[
                    UsageWindow(
                        label="Key",
                        used_percent=0 if status == "unavailable" else 100,
                        remaining_percent=100 if status == "ok" else 0,
                        detail=detail,
                    )
                ],
                error=None if status != "unavailable" else "Missing — tap Edit to add",
            )
        )

    return cards


def fetch_key_provider(cfg: dict[str, Any], env_name: str, display: str, pid: str) -> ProviderSnapshot:
    dev_root = Path(cfg.get("dev_root") or Path.home() / "dev")
    val = resolve_secret(env_name, dev_root)
    if not val:
        return ProviderSnapshot(pid, display, "unavailable", error="No API key on disk")
    return ProviderSnapshot(
        pid,
        display,
        "ok",
        plan="Free tier",
        windows=[
            UsageWindow(
                label="Key",
                used_percent=0,
                remaining_percent=100,
                detail=f"{mask_value(val)} — usage via ModelRouter",
            )
        ],
    )

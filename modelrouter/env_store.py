"""Atomic .env updates and provider key validation for connectors."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

# env_var → regex for value (full match)
_KEY_PATTERNS: dict[str, re.Pattern[str]] = {
    "GROQ_API_KEY": re.compile(r"^gsk_[A-Za-z0-9]{20,}$"),
    "ANTHROPIC_API_KEY": re.compile(r"^sk-ant-[A-Za-z0-9_-]{20,}$"),
    "OPENAI_API_KEY": re.compile(r"^sk-[A-Za-z0-9_-]{20,}$"),
    "MISTRAL_API_KEY": re.compile(r"^[A-Za-z0-9]{20,}$"),
}


def validate_provider_key(env_var: str, value: str) -> str | None:
    """Return an error message, or None if the key looks valid."""
    val = (value or "").strip()
    if not val:
        return f"{env_var} is empty"
    if any(ch.isspace() for ch in val):
        return f"{env_var} must not contain whitespace"
    pattern = _KEY_PATTERNS.get(env_var)
    if pattern and not pattern.fullmatch(val):
        hint = {
            "GROQ_API_KEY": "gsk_…",
            "ANTHROPIC_API_KEY": "sk-ant-…",
            "OPENAI_API_KEY": "sk-…",
        }.get(env_var, "provider format")
        return f"{env_var} does not match expected format ({hint})"
    if len(val) < 20:
        return f"{env_var} is too short"
    return None


def update_env_file(path: Path, key: str, value: str) -> None:
    """Atomically set or replace one KEY=value in a .env file."""
    path = Path(path)
    lines = path.read_text().splitlines() if path.exists() else []
    out: list[str] = []
    seen = False
    for line in lines:
        if line.startswith(f"{key}="):
            out.append(f"{key}={value}")
            seen = True
        else:
            out.append(line)
    if not seen:
        out.append(f"{key}={value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".env-{uuid.uuid4().hex}.tmp"
    tmp.write_text("\n".join(out) + "\n")
    tmp.replace(path)

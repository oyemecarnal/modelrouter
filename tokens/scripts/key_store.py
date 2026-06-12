"""Add API keys to tokens/.env.local (gitignored)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL_ENV = ROOT / ".env.local"

ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]{2,64}$")


def add_key(env_name: str, value: str) -> None:
    key = (env_name or "").strip().upper()
    val = (value or "").strip().strip("'\"")
    if not ENV_NAME.match(key):
        raise ValueError(f"Invalid env name: {key}")
    if not val or val.startswith("op://"):
        raise ValueError("Key value required")
    if len(val) < 8:
        raise ValueError("Key value too short")

    lines: list[str] = []
    if LOCAL_ENV.exists():
        lines = LOCAL_ENV.read_text().splitlines()

    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith(f"{key}="):
            out.append(f"{key}={val}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        if out and out[-1].strip():
            out.append("")
        out.append(f"{key}={val}")
    LOCAL_ENV.write_text("\n".join(out).rstrip() + "\n")

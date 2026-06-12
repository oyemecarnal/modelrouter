#!/usr/bin/env python3
"""
Load provider secrets into the environment before starting ModelRouter.

Priority per secret:
  1. Already set in environment (never overwritten)
  2. 1Password reference via `op read` (secrets.yaml)
  3. .env file values
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            if not value and key in ("DATABASE_URL", "DIRECT_URL"):
                continue
            os.environ[key] = value


def op_available() -> bool:
    try:
        subprocess.run(
            ["op", "--version"],
            capture_output=True,
            check=True,
            timeout=5,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def read_op(reference: str, account: str | None = None) -> str:
    args = ["read", reference, "--no-newline"]
    if account:
        args.extend(["--account", account])
    result = subprocess.run(args, capture_output=True, text=True, check=True, timeout=15)
    value = result.stdout.strip()
    if not value:
        raise RuntimeError(f"1Password returned empty value for {reference}")
    return value


def ensure_defaults() -> None:
    mk = os.environ.get("MODELROUTER_MASTER_KEY", "")
    if not mk or "change-me" in mk or mk == "sk-modelrouter-local-dev":
        if not mk:
            os.environ["MODELROUTER_MASTER_KEY"] = "sk-modelrouter-local-dev"
        print("[secrets] WARNING: MODELROUTER_MASTER_KEY is placeholder — run: make rotate-master-key")

    if not os.environ.get("LITELLM_SALT_KEY"):
        os.environ["LITELLM_SALT_KEY"] = os.environ["MODELROUTER_MASTER_KEY"]
        print("[secrets] WARNING: LITELLM_SALT_KEY unset — using master key (set distinct salt for Docker)")

    os.environ.setdefault("OLLAMA_API_BASE", "http://127.0.0.1:11434")
    os.environ.setdefault("REDIS_HOST", "127.0.0.1")
    os.environ.setdefault("REDIS_PORT", "6379")
    os.environ.setdefault("REDIS_PASSWORD", "")

    # Empty DATABASE_URL causes LiteLLM prisma warnings in minimal mode
    if os.environ.get("DATABASE_URL", "").strip() == "":
        os.environ.pop("DATABASE_URL", None)


def main() -> int:
    load_dotenv(ROOT / ".env")

    secrets_path = ROOT / "secrets.yaml"
    if not secrets_path.exists():
        secrets_path = ROOT / "secrets.example.yaml"

    secrets_cfg: dict = {}
    if secrets_path.exists():
        secrets_cfg = yaml.safe_load(secrets_path.read_text()) or {}

    account = os.environ.get("OP_ACCOUNT") or secrets_cfg.get("account")
    has_op = op_available()
    loaded: list[str] = []
    skipped: list[str] = []

    for env_var, reference in (secrets_cfg.get("secrets") or {}).items():
        if os.environ.get(env_var):
            skipped.append(env_var)
            continue

        if has_op and isinstance(reference, str) and reference.startswith("op://"):
            try:
                os.environ[env_var] = read_op(reference, account)
                loaded.append(f"{env_var} (1Password)")
            except subprocess.CalledProcessError as exc:
                print(f"[secrets] Failed to read {env_var} from 1Password: {exc.stderr}", file=sys.stderr)
        elif secrets_cfg.get("env_fallback", True):
            skipped.append(env_var)

    ensure_defaults()
    (ROOT / "data").mkdir(exist_ok=True)

    print(f"[secrets] 1Password CLI: {'available' if has_op else 'not found'}")
    if loaded:
        print(f"[secrets] Loaded: {', '.join(loaded)}")
    if skipped:
        print(f"[secrets] Using existing env for: {', '.join(skipped)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

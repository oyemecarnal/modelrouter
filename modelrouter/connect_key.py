"""Unified paste-key connector — one entry for all providers in config/connectors.yaml."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml

from modelrouter.env_store import update_env_file, validate_provider_key

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "config" / "connectors.yaml"


def load_connector(provider_id: str) -> dict:
    data = yaml.safe_load(REGISTRY.read_text()) or {}
    conn = (data.get("connectors") or {}).get(provider_id)
    if not conn:
        known = sorted((data.get("connectors") or {}).keys())
        raise SystemExit(f"Unknown provider: {provider_id}\nKnown: {', '.join(known)}")
    return conn


def save_key(env_file: Path, env_var: str, key: str, *, stash_alt: bool) -> None:
    err = validate_provider_key(env_var, key)
    if err:
        raise SystemExit(err)

    old: str | None = None
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith(f"{env_var}=") and not line.startswith(f"{env_var}__"):
                old = line.split("=", 1)[1].strip()
                break

    if stash_alt and old and old != key:
        update_env_file(env_file, f"{env_var}__ALT_1", old)
        print(f"  ok stashed previous key → {env_var}__ALT_1")

    update_env_file(env_file, env_var, key)
    print("  ok saved to .env (validated)")

    if stash_alt:
        subprocess.run(
            [sys.executable, "-m", "modelrouter.key_vault", "ingest-alts"],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            capture_output=True,
        )


def _env_has_key(env_file: Path, env_var: str) -> bool:
    if not env_file.exists():
        return False
    for line in env_file.read_text().splitlines():
        if line.startswith(f"{env_var}=") and not line.startswith(f"{env_var}__"):
            return bool(line.split("=", 1)[1].strip())
    return False


def read_key_interactive(env_var: str, env_file: Path, hint: str) -> str:
    if os.environ.get(env_var):
        print(f"Using {env_var} from environment.")
        return os.environ[env_var]

    if _env_has_key(env_file, env_var):
        replace = input(f"{env_var} already in .env. Replace? [y/N] ").strip().lower()
        if replace != "y":
            print("Keeping existing key (will still push/restart if enabled).")
            return ""

    import getpass

    return getpass.getpass(f"Paste {hint} ({env_var}): ")


def push_keys(env_file: Path, env_var: str, remote: str) -> None:
    print(f"── Push to {remote}")
    push_script = ROOT / "scripts" / "push-env-to-mini.sh"
    keys = [env_var]
    alt = f"{env_var}__ALT_1"
    if env_file.exists() and f"{alt}=" in env_file.read_text():
        keys.append(alt)
    subprocess.run([str(push_script), *keys], cwd=ROOT, check=False)


def restart_gateway(remote: str) -> None:
    print(f"── Restart gateway on {remote}")
    cmd = f"cd ~/dev/modelrouter && make restart"
    proc = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=5", remote, cmd],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        print("  ok mini gateway restarted")
    else:
        print(f"  warn mini restart failed — run: ssh {remote} '{cmd}'")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Paste-key connector for ModelRouter providers")
    parser.add_argument("provider", nargs="?", help="Connector id from config/connectors.yaml")
    parser.add_argument("--no-push", action="store_true")
    parser.add_argument("--no-restart", action="store_true")
    parser.add_argument("--stash-alt", action="store_true")
    parser.add_argument("--list", action="store_true", help="List known providers")
    args = parser.parse_args(argv)

    if args.list or not args.provider:
        data = yaml.safe_load(REGISTRY.read_text()) or {}
        for cid, c in sorted((data.get("connectors") or {}).items()):
            print(f"  {cid:12}  {c.get('label', cid)}  ({c.get('env', '')})")
        return 0 if args.list else 1

    conn = load_connector(args.provider)
    env_var = conn.get("env") or ""
    env_file = ROOT / ".env"
    remote = os.environ.get("MODELROUTER_REMOTE_HOST", "kc-mini-lan")
    push = not args.no_push and os.environ.get(f"CONNECT_{env_var}_PUSH", "1") != "0"
    restart = not args.no_restart and os.environ.get(f"CONNECT_{env_var}_RESTART", "1") != "0"

    print(f"==> Connect {conn.get('label', args.provider)} (ModelRouter)")
    if conn.get("signup"):
        print(f"    Signup: {conn['signup']}")
    if conn.get("presets"):
        print(f"    Presets: {', '.join(conn['presets'])}")
    print("    Docs: docs/CONNECTOR_SPEC.md")
    print()

    key = read_key_interactive(env_var, env_file, conn.get("label", env_var))
    if key:
        save_key(env_file, env_var, key, stash_alt=args.stash_alt)

    if push:
        print()
        push_keys(env_file, env_var, remote)
    else:
        print("── Skip push (--no-push)")

    if restart:
        print()
        restart_gateway(remote)
    else:
        print("── Skip restart (--no-restart)")

    print()
    print("==> Done. Verify: make check-key-hygiene && make doctor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

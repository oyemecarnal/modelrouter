"""Paste-key connector flow for widget — validate, save to modelrouter .env, optional mini push."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any


def _modelrouter_root(cfg: dict[str, Any]) -> Path:
    tokens_root = Path(__file__).resolve().parent.parent
    return Path(cfg.get("modelrouter_root") or tokens_root.parent)


def _load_connector(root: Path, provider_id: str) -> dict[str, str]:
    import yaml

    reg = yaml.safe_load((root / "config" / "connectors.yaml").read_text()) or {}
    conn = (reg.get("connectors") or {}).get(provider_id)
    if not conn:
        raise ValueError(f"unknown provider: {provider_id}")
    env_var = (conn or {}).get("env") or ""
    if not env_var:
        raise ValueError(f"connector {provider_id} missing env var")
    return {
        "id": provider_id,
        "env": env_var,
        "label": (conn or {}).get("label") or provider_id,
        "make": (conn or {}).get("make_target") or f"connect-{provider_id}",
    }


def paste_connector(
    cfg: dict[str, Any],
    provider_id: str,
    value: str,
    *,
    push: bool = True,
    restart: bool = True,
) -> dict[str, Any]:
    """Validate key, write modelrouter .env, optionally push to mini and restart."""
    root = _modelrouter_root(cfg)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from modelrouter.env_store import update_env_file, validate_provider_key

    conn = _load_connector(root, provider_id)
    env_var = conn["env"]
    key = (value or "").strip()
    err = validate_provider_key(env_var, key)
    if err:
        raise ValueError(err)

    env_path = root / ".env"
    update_env_file(env_path, env_var, key)

    result: dict[str, Any] = {
        "provider": provider_id,
        "env": env_var,
        "label": conn["label"],
        "pushed": False,
        "restarted": False,
    }

    remote_host = cfg.get("modelrouter_remote_host") or "kc-mini-lan"
    if push:
        push_script = root / "scripts" / "push-env-to-mini.sh"
        if not push_script.exists():
            raise RuntimeError("push-env-to-mini.sh missing")
        proc = subprocess.run(
            [str(push_script), env_var],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or "")[-400:]
            raise RuntimeError(f"push to mini failed: {tail.strip() or proc.returncode}")
        result["pushed"] = True

    if restart and push:
        proc = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=8", remote_host, "cd ~/dev/modelrouter && make restart"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        result["restarted"] = proc.returncode == 0

    return result

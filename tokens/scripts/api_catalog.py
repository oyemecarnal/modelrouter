"""Load API catalog and merge with on-disk key status."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from fetch_usage import resolve_secret
from key_inventory import KEY_LABELS, mask_value


def catalog_path(cfg: dict[str, Any] | None = None) -> Path:
    if cfg:
        root = Path(cfg.get("modelrouter_root") or Path.home() / "dev" / "modelrouter")
        return root / "config" / "api_catalog.yaml"
    return Path.home() / "dev" / "modelrouter" / "config" / "api_catalog.yaml"


def load_catalog(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    path = catalog_path(cfg)
    if not path.exists():
        return {"version": 1, "families": []}
    data = yaml.safe_load(path.read_text()) or {}
    data.setdefault("families", [])
    return data


def _key_status(env_name: str, dev_root: Path) -> dict[str, Any]:
    val = resolve_secret(env_name, dev_root)
    if val:
        return {"status": "ok", "masked": mask_value(val)}
    return {"status": "missing", "masked": None}


def catalog_with_status(cfg: dict[str, Any]) -> dict[str, Any]:
    cat = load_catalog(cfg)
    dev_root = Path(cfg.get("dev_root") or Path.home() / "dev")
    families_out: list[dict[str, Any]] = []

    for fam in cat.get("families") or []:
        keys_out: list[dict[str, Any]] = []
        for key_def in fam.get("keys") or []:
            if key_def.get("hidden"):
                continue
            env = key_def.get("env", "")
            st = _key_status(env, dev_root)
            keys_out.append(
                {
                    "env": env,
                    "label": key_def.get("label") or KEY_LABELS.get(env, env),
                    "signup": key_def.get("signup"),
                    "notes": key_def.get("notes"),
                    "free_tier": key_def.get("free_tier", False),
                    "pricing_ref": key_def.get("pricing_ref"),
                    "static_input_per_m": key_def.get("static_input_per_m"),
                    "static_output_per_m": key_def.get("static_output_per_m"),
                    **st,
                }
            )
        if not keys_out:
            continue
        configured = sum(1 for k in keys_out if k["status"] == "ok")
        families_out.append(
            {
                "id": fam.get("id"),
                "label": fam.get("label"),
                "purpose": fam.get("purpose"),
                "weight": fam.get("weight", 0.5),
                "repo_fit": fam.get("repo_fit") or [],
                "configured_count": configured,
                "total_count": len(keys_out),
                "coverage": round(configured / len(keys_out), 2) if keys_out else 0,
                "keys": keys_out,
            }
        )

    all_envs = {k["env"] for f in families_out for k in f["keys"]}
    configured_envs = {k["env"] for f in families_out for k in f["keys"] if k["status"] == "ok"}

    return {
        "version": cat.get("version", 1),
        "families": families_out,
        "summary": {
            "families": len(families_out),
            "keys_tracked": len(all_envs),
            "keys_configured": len(configured_envs),
        },
    }

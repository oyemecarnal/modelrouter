"""Read-only console grid for widget snapshot."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _root(cfg: dict[str, Any]) -> Path:
    return Path(cfg.get("modelrouter_root") or Path.home() / "dev" / "modelrouter")


def load_console_grid(cfg: dict[str, Any]) -> dict[str, Any]:
    root = _root(cfg)
    cat_path = root / "config" / "models_catalog.yaml"
    if not cat_path.exists():
        return {"presets": [], "models": [], "gateway_models": []}

    catalog = yaml.safe_load(cat_path.read_text()) or {}
    presets_out: list[dict[str, Any]] = []
    for pid, pinfo in sorted((catalog.get("presets") or {}).items()):
        if not isinstance(pinfo, dict):
            continue
        presets_out.append(
            {
                "id": pid,
                "label": pinfo.get("label") or pid,
                "cost_tier": pinfo.get("cost_tier"),
                "max_tokens": pinfo.get("max_tokens_default"),
                "clients": pinfo.get("clients") or [],
            }
        )

    models_out: list[dict[str, Any]] = []
    for mid, minfo in sorted((catalog.get("models") or {}).items()):
        if not isinstance(minfo, dict):
            continue
        models_out.append(
            {
                "id": mid,
                "provider": minfo.get("provider"),
                "context_window": minfo.get("context_window"),
                "cost_tier": minfo.get("cost_tier"),
                "billing": minfo.get("billing"),
            }
        )

    gateway_models: list[str] = []
    try:
        import os
        import urllib.request

        host = os.environ.get("MODELROUTER_HOST", "127.0.0.1")
        port = os.environ.get("MODELROUTER_PORT", "3000")
        if host in ("0.0.0.0", "::"):
            host = "127.0.0.1"
        key = os.environ.get("MODELROUTER_MASTER_KEY", "")
        if key:
            req = urllib.request.Request(
                f"http://{host}:{port}/v1/models",
                headers={"Authorization": f"Bearer {key}"},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                import json

                data = json.loads(resp.read().decode())
                gateway_models = [m["id"] for m in data.get("data", []) if m.get("id")]
    except Exception:
        gateway_models = []

    return {
        "catalog_version": catalog.get("catalog_version", 1),
        "presets": presets_out,
        "models": models_out,
        "gateway_models": gateway_models,
        "gateway_live": bool(gateway_models),
    }

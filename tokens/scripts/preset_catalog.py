"""Policy preset grid data from modelrouter models_catalog + projects."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

POLICY_PRESET_IDS = frozenset(
    {"cheap", "code", "review", "hermes-fast", "hermes-smart", "offline"}
)


def _modelrouter_root(cfg: dict[str, Any]) -> Path:
    return Path(cfg.get("modelrouter_root") or Path.home() / "dev" / "modelrouter")


def load_preset_catalog(cfg: dict[str, Any]) -> dict[str, Any]:
    root = _modelrouter_root(cfg)
    cat_path = root / "config" / "models_catalog.yaml"
    proj_path = root / "config" / "projects.yaml"
    if not cat_path.exists():
        return {"presets": [], "projects": []}

    catalog = yaml.safe_load(cat_path.read_text()) or {}
    projects_raw = {}
    if proj_path.exists():
        data = yaml.safe_load(proj_path.read_text()) or {}
        projects_raw = data.get("projects") or {}

    presets_out: list[dict[str, Any]] = []
    for pid, pinfo in sorted((catalog.get("presets") or {}).items()):
        if pid not in POLICY_PRESET_IDS or not isinstance(pinfo, dict):
            continue
        presets_out.append(
            {
                "id": pid,
                "label": pinfo.get("label") or pid,
                "description": pinfo.get("description") or "",
                "cost_tier": pinfo.get("cost_tier") or "—",
                "max_tokens": pinfo.get("max_tokens_default"),
                "clients": pinfo.get("clients") or [],
            }
        )

    projects_out: list[dict[str, Any]] = []
    for pid, pinfo in sorted(projects_raw.items()):
        if not isinstance(pinfo, dict):
            continue
        presets_map = pinfo.get("presets") or {}
        projects_out.append(
            {
                "id": pid,
                "description": pinfo.get("description") or "",
                "hosts": pinfo.get("hosts") or [],
                "presets": presets_map,
                "virtual_key_env": pinfo.get("virtual_key_env"),
            }
        )

    return {
        "catalog_version": catalog.get("catalog_version", 1),
        "presets": presets_out,
        "projects": projects_out,
    }

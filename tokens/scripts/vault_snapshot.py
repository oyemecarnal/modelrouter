"""Masked key vault inventory for widget snapshot — no secret values."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def _modelrouter_root(cfg: dict[str, Any]) -> Path:
    return Path(cfg.get("modelrouter_root") or Path.home() / "dev" / "modelrouter")


def load_vault_snapshot(cfg: dict[str, Any]) -> dict[str, Any]:
    root = _modelrouter_root(cfg)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from modelrouter.key_vault import list_entries, load_vault_config, vault_path

        vcfg = load_vault_config()
        rows = list_entries(vcfg)
        return {
            "enabled": True,
            "entries": rows,
            "count": len(rows),
            "vault_file": vault_path(vcfg).name,
        }
    except Exception as exc:
        return {"enabled": True, "error": str(exc)[:200], "entries": [], "count": 0}

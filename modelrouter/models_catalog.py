"""Load Phase 1 models catalog (config/models_catalog.yaml)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "config" / "models_catalog.yaml"


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    if not CATALOG_PATH.exists():
        return {}
    return yaml.safe_load(CATALOG_PATH.read_text()) or {}


def preset_names() -> list[str]:
    return sorted((load_catalog().get("presets") or {}).keys())


def preset_info(name: str) -> dict[str, Any] | None:
    return (load_catalog().get("presets") or {}).get(name)


def model_info(model_id: str) -> dict[str, Any] | None:
    return (load_catalog().get("models") or {}).get(model_id)

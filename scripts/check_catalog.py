#!/usr/bin/env python3
"""Verify models_catalog.yaml covers policy presets and referenced provider models."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "config" / "models_catalog.yaml"
PRESETS = ROOT / "config" / "includes" / "policy_presets.yaml"
POLICY_IDS = {"cheap", "code", "review", "hermes-fast", "hermes-smart", "offline"}


def first_max_tokens_per_preset() -> dict[str, int | None]:
    data = yaml.safe_load(PRESETS.read_text()) or {}
    seen: set[str] = set()
    out: dict[str, int | None] = {}
    for entry in data.get("preset_models") or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("model_name")
        if not name or name in seen:
            continue
        seen.add(name)
        params = entry.get("litellm_params") or {}
        mt = params.get("max_tokens")
        out[name] = int(mt) if mt is not None else None
    return out


def preset_names_from_policy() -> set[str]:
    data = yaml.safe_load(PRESETS.read_text()) or {}
    names: set[str] = set()
    for entry in data.get("preset_models") or []:
        if isinstance(entry, dict) and entry.get("model_name"):
            names.add(entry["model_name"])
    for fb in data.get("preset_fallbacks") or []:
        if isinstance(fb, dict):
            names.update(fb.keys())
    return names


def provider_models_from_policy() -> set[str]:
    data = yaml.safe_load(PRESETS.read_text()) or {}
    models: set[str] = set()
    for entry in data.get("preset_models") or []:
        if not isinstance(entry, dict):
            continue
        m = (entry.get("litellm_params") or {}).get("model")
        if m and "/" in str(m):
            models.add(str(m))
    return models


def main() -> int:
    if not CATALOG.exists():
        print(f"missing {CATALOG}", file=sys.stderr)
        return 1
    cat = yaml.safe_load(CATALOG.read_text()) or {}
    catalog_presets = set((cat.get("presets") or {}).keys())
    catalog_models = set((cat.get("models") or {}).keys())

    ok = True
    for name in sorted(preset_names_from_policy()):
        if name not in catalog_presets:
            print(f"  FAIL catalog missing preset: {name}", file=sys.stderr)
            ok = False
    for model in sorted(provider_models_from_policy()):
        if model not in catalog_models:
            print(f"  FAIL catalog missing model: {model}", file=sys.stderr)
            ok = False

    cat_limits = {
        k: int(v.get("max_tokens_default"))
        for k, v in (cat.get("presets") or {}).items()
        if isinstance(v, dict) and k in POLICY_IDS and v.get("max_tokens_default") is not None
    }
    applied = first_max_tokens_per_preset()
    for pid in sorted(POLICY_IDS):
        want = cat_limits.get(pid)
        if want is None:
            continue
        got = applied.get(pid)
        if got != want:
            print(
                f"  FAIL policy_presets primary {pid}: max_tokens={got} want {want} (run sync-preset-tokens)",
                file=sys.stderr,
            )
            ok = False

    if ok:
        print(f"  ok models_catalog.yaml ({len(catalog_presets)} presets, {len(catalog_models)} models)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

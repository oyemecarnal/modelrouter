#!/usr/bin/env python3
"""Verify policy preset names in gateway configs match config/includes/policy_presets.yaml."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
INCLUDES = ROOT / "config" / "includes" / "policy_presets.yaml"
CONFIGS = [
    ROOT / "config" / "modelrouter.minimal.yaml",
    ROOT / "config" / "modelrouter.yaml",
]


def preset_names_from_includes() -> set[str]:
    data = yaml.safe_load(INCLUDES.read_text()) or {}
    names: set[str] = set()
    for entry in data.get("preset_models") or []:
        if isinstance(entry, dict) and entry.get("model_name"):
            names.add(entry["model_name"])
    for fb in data.get("preset_fallbacks") or []:
        if isinstance(fb, dict):
            names.update(fb.keys())
    return names


def preset_names_in_config(path: Path) -> set[str]:
    data = yaml.safe_load(path.read_text()) or {}
    names: set[str] = set()
    for entry in data.get("model_list") or []:
        mn = entry.get("model_name")
        if mn in {
            "cheap", "code", "review", "hermes-fast", "hermes-smart", "offline",
        }:
            names.add(mn)
    return names


def main() -> int:
    if not INCLUDES.exists():
        print(f"missing {INCLUDES}", file=sys.stderr)
        return 1
    expected = preset_names_from_includes()
    ok = True
    for cfg in CONFIGS:
        if not cfg.exists():
            continue
        found = preset_names_in_config(cfg)
        missing = expected - found
        if missing:
            print(f"  FAIL {cfg.name}: missing presets {sorted(missing)}", file=sys.stderr)
            ok = False
        else:
            print(f"  ok {cfg.name} presets")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

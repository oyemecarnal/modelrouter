#!/usr/bin/env python3
"""Ensure primary policy preset routes have max_tokens from models_catalog.yaml."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "config" / "models_catalog.yaml"
TARGETS = [
    ROOT / "config" / "includes" / "policy_presets.yaml",
    ROOT / "config" / "modelrouter.minimal.yaml",
    ROOT / "config" / "modelrouter.yaml",
]
POLICY_IDS = {"cheap", "code", "review", "hermes-fast", "hermes-smart", "offline"}


def catalog_limits() -> dict[str, int]:
    cat = yaml.safe_load(CATALOG.read_text()) or {}
    out: dict[str, int] = {}
    for pid, pinfo in (cat.get("presets") or {}).items():
        if pid not in POLICY_IDS or not isinstance(pinfo, dict):
            continue
        mt = pinfo.get("max_tokens_default")
        if mt is not None:
            out[pid] = int(mt)
    return out


def patch_file(path: Path, limits: dict[str, int]) -> int:
    lines = path.read_text().splitlines(keepends=True)
    out: list[str] = []
    i = 0
    changed = 0
    seen: set[str] = set()

    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(\s+)- model_name: (\S+)", line)
        if m and m.group(2) in limits and m.group(2) not in seen:
            preset = m.group(2)
            seen.add(preset)
            block = [line]
            j = i + 1
            in_litellm = False
            has_max = False
            key_line_idx: int | None = None
            while j < len(lines):
                nl = lines[j]
                if re.match(r"^\s+- model_name:", nl):
                    break
                if re.match(r"^[a-zA-Z#]", nl) and not nl.startswith(" "):
                    break
                block.append(nl)
                if "litellm_params:" in nl:
                    in_litellm = True
                if in_litellm and "max_tokens:" in nl:
                    has_max = True
                if in_litellm and re.match(r"^\s+(api_key|api_base):", nl):
                    key_line_idx = len(block) - 1
                j += 1
            if not has_max and key_line_idx is not None:
                key_line = block[key_line_idx]
                indent = re.match(r"^(\s+)", key_line)
                pad = indent.group(1) if indent else "      "
                block.insert(key_line_idx + 1, f"{pad}max_tokens: {limits[preset]}\n")
                changed += 1
            out.extend(block)
            i = j
            continue
        out.append(line)
        i += 1

    if changed:
        path.write_text("".join(out))
    return changed


def main() -> int:
    if not CATALOG.exists():
        print(f"missing {CATALOG}", file=sys.stderr)
        return 1
    limits = catalog_limits()
    total = 0
    for path in TARGETS:
        if not path.exists():
            print(f"  skip missing {path.name}")
            continue
        n = patch_file(path, limits)
        if n:
            print(f"  patched {path.name}: {n} max_tokens")
            total += n
        else:
            print(f"  ok {path.name}")
    if total:
        print(f"[sync-preset-tokens] updated {total} entries")
    else:
        print("[sync-preset-tokens] already in sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate modelrouter.yaml / modelrouter.minimal.yaml from base + policy_presets SSOT."""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
GATEWAY_DIR = ROOT / "config" / "gateway"
PRESETS = ROOT / "config" / "includes" / "policy_presets.yaml"
CATALOG = ROOT / "config" / "models_catalog.yaml"
OUTPUTS = {
    "full": (GATEWAY_DIR / "modelrouter.base.yaml", ROOT / "config" / "modelrouter.yaml"),
    "minimal": (
        GATEWAY_DIR / "modelrouter.minimal.base.yaml",
        ROOT / "config" / "modelrouter.minimal.yaml",
    ),
}
POLICY_IDS = frozenset({"cheap", "code", "review", "hermes-fast", "hermes-smart", "offline", "be-manager"})
GENERATED_HEADER = (
    "# GENERATED — do not edit preset routes here.\n"
    "# SSOT: config/includes/policy_presets.yaml\n"
    "# Regenerate: make sync-gateway-config\n\n"
)
ALT_SUFFIX = "__ALT_1"


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text()) or {}


def catalog_limits() -> dict[str, int]:
    cat = _load(CATALOG)
    out: dict[str, int] = {}
    for pid, pinfo in (cat.get("presets") or {}).items():
        if pid not in POLICY_IDS or not isinstance(pinfo, dict):
            continue
        mt = pinfo.get("max_tokens_default")
        if mt is not None:
            out[pid] = int(mt)
    return out


def apply_catalog_max_tokens(preset_models: list[dict[str, Any]], limits: dict[str, int]) -> None:
    seen: set[str] = set()
    for entry in preset_models:
        name = entry.get("model_name")
        if name not in limits or name in seen:
            continue
        seen.add(name)
        params = entry.setdefault("litellm_params", {})
        if "max_tokens" not in params:
            params["max_tokens"] = limits[name]


def expand_alt_routes(preset_models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mirror primary provider routes with VAR__ALT_1 keys for vault shuffle."""
    out: list[dict[str, Any]] = []
    for entry in preset_models:
        out.append(entry)
        params = entry.get("litellm_params") or {}
        api_key = params.get("api_key", "")
        if not api_key.startswith("os.environ/"):
            continue
        env_var = api_key.split("/", 1)[1]
        if env_var.endswith(ALT_SUFFIX) or "OLLAMA" in env_var:
            continue
        alt = copy.deepcopy(entry)
        alt_params = alt.setdefault("litellm_params", {})
        alt_params["api_key"] = f"os.environ/{env_var}{ALT_SUFFIX}"
        out.append(alt)
    return out


def merge_fallbacks(base_fb: list[Any], preset_fb: list[Any]) -> list[Any]:
    preset_names: set[str] = set()
    for item in preset_fb:
        if isinstance(item, dict):
            preset_names.update(item.keys())
    kept: list[Any] = []
    for item in base_fb:
        if isinstance(item, dict):
            keys = set(item.keys())
            if keys & preset_names:
                continue
        kept.append(item)
    return kept + list(preset_fb)


def _resolved_preset_models() -> list[dict[str, Any]]:
    """
    Try to generate preset model entries from the semantic intent resolver.
    Falls back to the static policy_presets.yaml if the resolver errors or
    produces no output (e.g. no keys configured yet).
    """
    try:
        resolver_path = str(ROOT)
        if resolver_path not in sys.path:
            sys.path.insert(0, resolver_path)
        from modelrouter.preset_resolver import build_model_list

        resolved = build_model_list()
        if resolved:
            print(f"  resolver: {len(resolved)} entries from preset_intents.yaml")
            return resolved
    except Exception as exc:
        print(f"  resolver unavailable ({exc}), falling back to static presets", file=sys.stderr)
    return []


def build_config(base_path: Path, out_path: Path, *, check_only: bool) -> bool:
    base = _load(base_path)
    presets_data = _load(PRESETS)

    # Use the semantic resolver if it produces output; otherwise fall back to static YAML
    resolved_models = _resolved_preset_models()
    if resolved_models:
        preset_models = resolved_models
    else:
        preset_models = copy.deepcopy(presets_data.get("preset_models") or [])

    preset_fallbacks = presets_data.get("preset_fallbacks") or []

    limits = catalog_limits()
    apply_catalog_max_tokens(preset_models, limits)
    preset_models = expand_alt_routes(preset_models)

    merged = copy.deepcopy(base)
    base_list = merged.get("model_list") or []
    merged["model_list"] = base_list + preset_models

    litellm = merged.setdefault("litellm_settings", {})
    base_fb = litellm.get("fallbacks") or []
    litellm["fallbacks"] = merge_fallbacks(base_fb, preset_fallbacks)

    rendered = GENERATED_HEADER + yaml.dump(
        merged,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    if check_only:
        if not out_path.exists():
            print(f"  FAIL missing {out_path.name} — run make sync-gateway-config", file=sys.stderr)
            return False
        current = out_path.read_text()
        if current != rendered:
            print(f"  FAIL {out_path.name} stale — run make sync-gateway-config", file=sys.stderr)
            return False
        print(f"  ok {out_path.name} (generated, fresh)")
        return True

    out_path.write_text(rendered)
    print(f"  wrote {out_path.relative_to(ROOT)} ({len(preset_models)} preset routes)")
    return True


def main() -> int:
    check_only = "--check" in sys.argv
    if not PRESETS.exists():
        print(f"missing {PRESETS}", file=sys.stderr)
        return 1

    ok = True
    for label, (base_path, out_path) in OUTPUTS.items():
        if not base_path.exists():
            print(f"missing base {base_path}", file=sys.stderr)
            ok = False
            continue
        if not build_config(base_path, out_path, check_only=check_only):
            ok = False

    if not check_only:
        print("[sync-gateway-config] done")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

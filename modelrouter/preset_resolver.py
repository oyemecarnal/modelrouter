"""
Semantic preset resolver — maps intent names to real models based on what's
actually available (configured keys, provider health, rate-limit pressure).

This is the "framework for item 1": clients say `cheap`, `smart`, `code` etc.
The resolver determines which concrete models should back each intent right now,
in priority order, without the client ever specifying a provider or model name.

USAGE
-----
    from modelrouter.preset_resolver import resolve, resolve_all, build_model_list

    # Single intent → ordered list of (model_string, reason) pairs
    models = resolve("smart")
    # [("anthropic/claude-sonnet-4-20250514", "family=anthropic tier=3 key=ok"),
    #  ("openai/gpt-4o", "family=openai tier=4 key=ok"), ...]

    # All intents → dict used to regenerate gateway YAML
    all_resolved = resolve_all()

    # Generate model_list entries suitable for litellm config
    entries = build_model_list()

INTEGRATION
-----------
    make sync-gateway-config  →  calls sync_gateway_config.py  →  calls resolve_all()
    The YAML output replaces the preset_models block in policy_presets.yaml.

RESOLUTION LOGIC
----------------
1. Load intent definitions from config/preset_intents.yaml
2. Load family definitions from config/model_families.yaml
3. For each intent:
   a. Walk the intent's family_preference list
   b. Within each family, walk tiers from highest→lowest quality
   c. Skip tiers above intent's max_cost_tier
   d. Skip models whose provider env var is not set in .env
   e. Apply current rate-limit pressure (from route_hints.json) to deprioritize hot providers
   f. If enterprise mode is on and intent.enterprise_lock, only include the first family
4. Output ordered candidate list with reasoning attached
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
INTENTS_CONFIG  = ROOT / "config" / "preset_intents.yaml"
FAMILIES_CONFIG = ROOT / "config" / "model_families.yaml"
ROUTE_HINTS     = ROOT / "data" / "route_hints.json"
ENV_FILE        = ROOT / ".env"

# Provider env var names (used to check if a key is configured)
_PROVIDER_ENV: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai":    "OPENAI_API_KEY",
    "groq":      "GROQ_API_KEY",
    "google":    "GOOGLE_API_KEY",
    "mistral":   "MISTRAL_API_KEY",
    "deepseek":  "DEEPSEEK_API_KEY",
    "together":  "TOGETHER_API_KEY",
    "fireworks": "FIREWORKS_AI_API_KEY",
    "local":     None,  # Ollama — no key needed
}

_PROVIDER_LITELLM_KEY_REF: dict[str, str] = {
    "anthropic": "os.environ/ANTHROPIC_API_KEY",
    "openai":    "os.environ/OPENAI_API_KEY",
    "groq":      "os.environ/GROQ_API_KEY",
    "google":    "os.environ/GOOGLE_API_KEY",
    "mistral":   "os.environ/MISTRAL_API_KEY",
    "deepseek":  "os.environ/DEEPSEEK_API_KEY",
    "together":  "os.environ/TOGETHER_API_KEY",
    "fireworks": "os.environ/FIREWORKS_AI_API_KEY",
    "local":     None,
}


# ── Config loading ─────────────────────────────────────────────────────────────

def _load_intents() -> dict[str, Any]:
    if not INTENTS_CONFIG.exists():
        return {}
    return (yaml.safe_load(INTENTS_CONFIG.read_text()) or {}).get("intents") or {}


def _load_families() -> dict[str, Any]:
    if not FAMILIES_CONFIG.exists():
        return {}
    return yaml.safe_load(FAMILIES_CONFIG.read_text()) or {}


# ── Key / provider availability ────────────────────────────────────────────────

def _load_env_keys() -> dict[str, str]:
    """Read key=value pairs from .env, return as dict (values may be empty)."""
    keys: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(errors="replace").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            keys[k.strip()] = v.strip()
    # Also pick up anything already in the process environment
    for k, v in os.environ.items():
        if k not in keys:
            keys[k] = v
    return keys


def _provider_available(provider: str, env_keys: dict[str, str]) -> bool:
    """True if the provider has a non-empty key configured (or is local/Ollama)."""
    env_var = _PROVIDER_ENV.get(provider)
    if env_var is None:
        return True  # local — no key needed
    val = env_keys.get(env_var, "")
    return bool(val and val not in ("", "your_key_here", "sk-change-me"))


# ── Rate-limit pressure ────────────────────────────────────────────────────────

def _load_pressure() -> dict[str, float]:
    """0 = fine, 100 = exhausted. Sourced from route_hints.json written by route_policy."""
    if not ROUTE_HINTS.exists():
        return {}
    try:
        data = json.loads(ROUTE_HINTS.read_text())
        # route_hints may be a single project dict or a dict of project → hint
        if "pressure" in data:
            return data["pressure"]
        # multi-project form: aggregate across projects
        combined: dict[str, float] = {}
        for project_data in data.values():
            if isinstance(project_data, dict):
                for k, v in (project_data.get("pressure") or {}).items():
                    combined[k] = max(combined.get(k, 0.0), float(v))
        return combined
    except (json.JSONDecodeError, OSError):
        return {}


def _provider_pressure(provider: str, pressure: dict[str, float]) -> float:
    """Return the highest pressure reading for any key belonging to this provider."""
    mapping = {
        "openai":    ["openai-codex", "gpt-4o"],
        "anthropic": ["anthropic"],
        "groq":      ["groq"],
        "google":    ["gemini", "google"],
        "mistral":   ["mistral"],
        "deepseek":  ["deepseek"],
    }
    keys = mapping.get(provider, [provider])
    return max((pressure.get(k, 0.0) for k in keys), default=0.0)


# ── Core resolver ──────────────────────────────────────────────────────────────

class ResolvedModel:
    __slots__ = ("model", "family", "provider", "cost_tier", "key_ref", "reason")

    def __init__(
        self,
        model: str,
        family: str,
        provider: str,
        cost_tier: int,
        key_ref: str | None,
        reason: str,
    ) -> None:
        self.model     = model
        self.family    = family
        self.provider  = provider
        self.cost_tier = cost_tier
        self.key_ref   = key_ref
        self.reason    = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "model":     self.model,
            "family":    self.family,
            "provider":  self.provider,
            "cost_tier": self.cost_tier,
            "reason":    self.reason,
        }


def resolve(
    intent_name: str,
    *,
    enterprise_mode: bool = False,
    env_keys: dict[str, str] | None = None,
    pressure: dict[str, float] | None = None,
) -> list[ResolvedModel]:
    """
    Resolve an intent name → ordered list of ResolvedModel candidates.

    enterprise_mode=True: if the intent has enterprise_lock=true, only the
    first family_preference entry is considered.
    """
    intents  = _load_intents()
    families = _load_families()
    fam_map: dict[str, Any] = families.get("families") or {}

    intent = intents.get(intent_name)
    if not intent:
        return []

    if env_keys is None:
        env_keys = _load_env_keys()
    if pressure is None:
        pressure = _load_pressure()

    max_cost = int(intent.get("max_cost_tier") or 5)
    family_pref: list[str] = intent.get("family_preference") or []
    locked = enterprise_mode and bool(intent.get("enterprise_lock"))

    if locked:
        family_pref = family_pref[:1]

    candidates: list[ResolvedModel] = []

    for fam_name in family_pref:
        fam = fam_map.get(fam_name)
        if not fam:
            continue
        provider: str = fam.get("provider") or fam_name
        if not _provider_available(provider, env_keys):
            continue

        tiers: list[dict[str, Any]] = sorted(
            fam.get("tiers") or [],
            key=lambda t: -int(t.get("cost_tier") or 0),
        )
        pres = _provider_pressure(provider, pressure)

        for tier in tiers:
            cost_tier = int(tier.get("cost_tier") or 0)
            if cost_tier > max_cost:
                continue
            model_str = tier.get("model")
            if not model_str:
                continue

            key_ref = _PROVIDER_LITELLM_KEY_REF.get(provider)
            reason_parts = [f"family={fam_name}", f"tier={cost_tier}"]
            if pres > 60:
                reason_parts.append(f"pressure={pres:.0f}%")
            if locked:
                reason_parts.append("enterprise-locked")

            candidates.append(ResolvedModel(
                model=model_str,
                family=fam_name,
                provider=provider,
                cost_tier=cost_tier,
                key_ref=key_ref,
                reason=" ".join(reason_parts),
            ))

    # Deprioritize models from high-pressure providers by moving them to the end
    # (stable sort — low-pressure first, then high-pressure within same cost tier)
    candidates.sort(key=lambda c: (
        _provider_pressure(c.provider, pressure) > 60,  # hot providers last
        -c.cost_tier if intent.get("latency") == "instant" else 0,
    ))

    return candidates


def resolve_all(*, enterprise_mode: bool = False) -> dict[str, list[ResolvedModel]]:
    """Resolve every defined intent. Returns {intent_name: [ResolvedModel, ...]}."""
    intents = _load_intents()
    env_keys = _load_env_keys()
    pressure = _load_pressure()
    return {
        name: resolve(name, enterprise_mode=enterprise_mode, env_keys=env_keys, pressure=pressure)
        for name in intents
    }


# ── LiteLLM config builder ─────────────────────────────────────────────────────

def build_model_list(*, enterprise_mode: bool = False) -> list[dict[str, Any]]:
    """
    Build the model_list entries for litellm config YAML.

    Each ResolvedModel becomes a model_list entry with model_name = intent name
    and litellm_params pointing at the resolved concrete model.
    """
    all_resolved = resolve_all(enterprise_mode=enterprise_mode)
    entries: list[dict[str, Any]] = []

    for intent_name, candidates in all_resolved.items():
        intents = _load_intents()
        intent = intents.get(intent_name) or {}

        for candidate in candidates:
            params: dict[str, Any] = {"model": candidate.model}
            if candidate.key_ref:
                params["api_key"] = candidate.key_ref
            if intent.get("context_window"):
                params["max_tokens"] = min(int(intent["context_window"]), 8192)

            entry: dict[str, Any] = {
                "model_name": intent_name,
                "litellm_params": params,
                "model_info": {
                    "mode": "chat",
                    "description": (
                        f"{intent.get('display', intent_name)} — "
                        f"{candidate.family}/{candidate.model.split('/')[-1]} "
                        f"({candidate.reason})"
                    ),
                },
            }
            if intent.get("requires", {}).get("function_calling"):
                entry["model_info"]["supports_function_calling"] = True
            entries.append(entry)

    return entries


def intent_summary() -> list[dict[str, Any]]:
    """
    Return a human-readable summary of all intents and their resolved models.
    Useful for the widget, Raycast extension, or CLI.
    """
    all_resolved = resolve_all()
    intents = _load_intents()
    out = []
    for name, candidates in all_resolved.items():
        intent = intents.get(name) or {}
        out.append({
            "name": name,
            "display": intent.get("display", name),
            "description": intent.get("description", ""),
            "latency": intent.get("latency", "normal"),
            "max_cost_tier": intent.get("max_cost_tier", 5),
            "enterprise_lock": bool(intent.get("enterprise_lock")),
            "resolved": [c.to_dict() for c in candidates[:4]],
            "available": len(candidates) > 0,
        })
    return out


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Semantic preset resolver")
    sub = parser.add_subparsers(dest="cmd")

    res_p = sub.add_parser("resolve", help="Resolve a single intent")
    res_p.add_argument("intent")
    res_p.add_argument("--enterprise", action="store_true")

    sub.add_parser("all", help="Resolve all intents")
    sub.add_parser("summary", help="Human-readable intent summary")
    sub.add_parser("model-list", help="Output litellm model_list YAML block")

    args = parser.parse_args()

    if args.cmd == "resolve":
        models = resolve(args.intent, enterprise_mode=getattr(args, "enterprise", False))
        print(json.dumps([m.to_dict() for m in models], indent=2))
    elif args.cmd == "all":
        result = {k: [m.to_dict() for m in v] for k, v in resolve_all().items()}
        print(json.dumps(result, indent=2))
    elif args.cmd == "summary":
        print(json.dumps(intent_summary(), indent=2))
    elif args.cmd == "model-list":
        entries = build_model_list()
        print(yaml.dump(entries, default_flow_style=False, sort_keys=False))
    else:
        parser.print_help()

"""
Same-family model routing and enterprise mode state.

ROUTING DISCIPLINE
==================
When routing to a cheaper fallback, stay within the same model family
(provider) rather than crossing providers. If the whole family is exhausted,
cross-family fallback is allowed unless enterprise mode is active.

ENTERPRISE MODE
===============
When enterprise mode is ON:
  - Each preset is locked to its designated family (see config/model_families.yaml).
  - Cross-family routing is blocked.
  - A "handoff" — an explicit one-shot override to a different family — can be
    triggered via allow_handoff() or the /enterprise/handoff API endpoint.
    After the handoff completes (one request), the lock is restored.

When enterprise mode is OFF (default):
  - Same-family fallback is still preferred, but cross-family is allowed when
    the whole family is exhausted.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
FAMILIES_CONFIG = ROOT / "config" / "model_families.yaml"
STATE_PATH = ROOT / "data" / "enterprise_state.json"


# ── config loading ────────────────────────────────────────────────────────────

def _load_families() -> dict[str, Any]:
    if not FAMILIES_CONFIG.exists():
        return {}
    return yaml.safe_load(FAMILIES_CONFIG.read_text()) or {}


def families() -> dict[str, Any]:
    """Return the families config dict (cached per process)."""
    return _load_families()


def family_for_model(model: str) -> str | None:
    """Return the family name for a model string like 'anthropic/claude-sonnet-4-20250514'."""
    cfg = families()
    provider = model.split("/")[0] if "/" in model else model
    for name, fam in (cfg.get("families") or {}).items():
        if fam.get("provider") == provider:
            return name
        for tier in fam.get("tiers") or []:
            if tier.get("model") == model or tier.get("id") == model:
                return name
    return None


def same_family_fallbacks(model: str, *, exclude: list[str] | None = None) -> list[str]:
    """
    Return cheaper-tier model IDs in the same family as `model`, sorted from
    cheapest to next-cheapest (so the router tries them in order).

    E.g.: same_family_fallbacks("anthropic/claude-opus-4-8")
          → ["anthropic/claude-haiku-4-5-20251001", "anthropic/claude-sonnet-4-20250514"]
    """
    cfg = families()
    excl = set(exclude or [])
    fam_name = family_for_model(model)
    if not fam_name:
        return []
    fam = (cfg.get("families") or {}).get(fam_name, {})
    tiers: list[dict[str, Any]] = fam.get("tiers") or []

    # Find the cost_tier of the requested model
    current_cost = None
    for t in tiers:
        if t.get("model") == model or t.get("id") == model:
            current_cost = t.get("cost_tier", 0)
            break
    if current_cost is None:
        return []

    # Collect cheaper tiers, sorted cheapest-first
    cheaper = [t for t in tiers if t.get("cost_tier", 0) < current_cost and t.get("model") not in excl]
    cheaper.sort(key=lambda t: t.get("cost_tier", 0))
    return [t["model"] for t in cheaper if "model" in t]


def fallback_chain_for_preset(preset: str, *, enterprise: bool = False) -> list[str]:
    """
    Build a complete fallback chain for a preset.

    enterprise=True  → same-family only (no cross-provider)
    enterprise=False → same-family first, then cross-family
    """
    cfg = families()
    preset_families_cfg: dict[str, list[str]] = cfg.get("preset_families") or {}
    family_names = preset_families_cfg.get(preset) or []
    fam_map: dict[str, Any] = cfg.get("families") or {}

    chain: list[str] = []
    seen: set[str] = set()

    def add(m: str) -> None:
        if m not in seen:
            seen.add(m)
            chain.append(m)

    # Within each designated family, walk tiers from most capable → cheapest
    for fname in family_names:
        fam = fam_map.get(fname, {})
        tiers = sorted(fam.get("tiers") or [], key=lambda t: -t.get("cost_tier", 0))
        for t in tiers:
            if "model" in t:
                add(t["model"])
        if enterprise:
            break  # locked to first family only

    return chain


# ── enterprise state ──────────────────────────────────────────────────────────

_DEFAULT_STATE: dict[str, Any] = {
    "enterprise_mode": False,
    "handoff_allowed": False,
    "handoff_target_family": None,
    "handoff_expires_at": None,
    "locked_family": None,
    "updated_at": None,
}


def _read_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return dict(_DEFAULT_STATE)
    try:
        data = json.loads(STATE_PATH.read_text())
        return {**_DEFAULT_STATE, **data}
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_STATE)


def _write_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = int(time.time() * 1000)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


def get_state() -> dict[str, Any]:
    """Return current enterprise state (reads from disk each call)."""
    state = _read_state()
    # Expire handoffs automatically
    if state.get("handoff_expires_at") and time.time() > state["handoff_expires_at"]:
        state["handoff_allowed"] = False
        state["handoff_target_family"] = None
        state["handoff_expires_at"] = None
        _write_state(state)
    return state


def set_enterprise_mode(enabled: bool, *, locked_family: str | None = None) -> dict[str, Any]:
    """
    Enable or disable enterprise mode.

    When enabling, optionally lock to a specific family name (e.g. "anthropic").
    If no family is specified the lock is determined per-preset from config.
    """
    state = _read_state()
    state["enterprise_mode"] = enabled
    state["locked_family"] = locked_family if enabled else None
    if not enabled:
        # Clear any pending handoff when turning off enterprise mode
        state["handoff_allowed"] = False
        state["handoff_target_family"] = None
        state["handoff_expires_at"] = None
    _write_state(state)
    return state


def allow_handoff(
    target_family: str | None = None,
    *,
    ttl_seconds: float = 120,
) -> dict[str, Any]:
    """
    Grant a one-shot handoff in enterprise mode.

    target_family: which family to route to (None = any family allowed)
    ttl_seconds:   how long the handoff window stays open (default 2 min)

    The handoff expires after ttl_seconds OR after the next routed request,
    whichever comes first. The caller (UI, API) is responsible for consuming it.
    """
    state = _read_state()
    if not state.get("enterprise_mode"):
        return {**state, "error": "Enterprise mode is not active"}
    state["handoff_allowed"] = True
    state["handoff_target_family"] = target_family
    state["handoff_expires_at"] = time.time() + ttl_seconds
    _write_state(state)
    return state


def consume_handoff() -> dict[str, Any]:
    """
    Called by the router when a cross-family request is made under a handoff.
    Clears the handoff flag so subsequent requests return to the locked family.
    """
    state = _read_state()
    state["handoff_allowed"] = False
    state["handoff_target_family"] = None
    state["handoff_expires_at"] = None
    _write_state(state)
    return state


def cancel_handoff() -> dict[str, Any]:
    """Cancel a pending handoff without consuming it."""
    return consume_handoff()


# ── routing decision helper ───────────────────────────────────────────────────

def routing_decision(
    requested_model: str,
    *,
    preferred_family: str | None = None,
) -> dict[str, Any]:
    """
    Given a requested model (or preset name), return the routing decision:

    {
      "model": str,              # model to actually use
      "family": str | None,      # resolved family
      "enterprise_mode": bool,
      "handoff_active": bool,
      "same_family_fallbacks": [...],   # cheaper fallbacks within family
      "cross_family_allowed": bool,
    }
    """
    state = get_state()
    ent = state.get("enterprise_mode", False)
    handoff = state.get("handoff_allowed", False)
    locked = state.get("locked_family") or preferred_family
    fam = family_for_model(requested_model) or locked

    return {
        "model": requested_model,
        "family": fam,
        "enterprise_mode": ent,
        "handoff_active": handoff,
        "handoff_target_family": state.get("handoff_target_family"),
        "same_family_fallbacks": same_family_fallbacks(requested_model),
        "cross_family_allowed": (not ent) or handoff,
        "locked_family": locked,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ModelRouter family router")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("state", help="Show current enterprise state")
    on_p = sub.add_parser("on", help="Enable enterprise mode")
    on_p.add_argument("--family", help="Lock to a specific family")
    sub.add_parser("off", help="Disable enterprise mode")
    ho_p = sub.add_parser("handoff", help="Allow one-shot handoff")
    ho_p.add_argument("--family", help="Target family (default: any)")
    ho_p.add_argument("--ttl", type=float, default=120, help="Seconds before auto-expiry")
    sub.add_parser("cancel-handoff", help="Cancel pending handoff")
    fb_p = sub.add_parser("fallbacks", help="Show same-family fallbacks for a model")
    fb_p.add_argument("model")
    chain_p = sub.add_parser("chain", help="Show full fallback chain for a preset")
    chain_p.add_argument("preset")
    chain_p.add_argument("--enterprise", action="store_true")

    args = parser.parse_args()

    if args.cmd == "state":
        print(json.dumps(get_state(), indent=2))
    elif args.cmd == "on":
        print(json.dumps(set_enterprise_mode(True, locked_family=getattr(args, "family", None)), indent=2))
    elif args.cmd == "off":
        print(json.dumps(set_enterprise_mode(False), indent=2))
    elif args.cmd == "handoff":
        print(json.dumps(allow_handoff(getattr(args, "family", None), ttl_seconds=args.ttl), indent=2))
    elif args.cmd == "cancel-handoff":
        print(json.dumps(cancel_handoff(), indent=2))
    elif args.cmd == "fallbacks":
        print(json.dumps(same_family_fallbacks(args.model), indent=2))
    elif args.cmd == "chain":
        print(json.dumps(fallback_chain_for_preset(args.preset, enterprise=args.enterprise), indent=2))
    else:
        parser.print_help()

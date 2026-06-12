"""Cost comparator — live OpenRouter pricing + static catalog, per-family rankings."""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from typing import Any

from api_catalog import catalog_with_status, load_catalog

OPENROUTER_MODELS = "https://openrouter.ai/api/v1/models"
CACHE_TTL = 3600
_price_cache: dict[str, Any] = {"at": 0, "models": {}}


def _fetch_openrouter_prices() -> dict[str, dict[str, float]]:
    now = time.time()
    if _price_cache["models"] and now - _price_cache["at"] < CACHE_TTL:
        return _price_cache["models"]

    models: dict[str, dict[str, float]] = {}
    try:
        req = urllib.request.Request(
            OPENROUTER_MODELS,
            headers={"Accept": "application/json", "User-Agent": "ModelRouter-Keys/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        for m in data.get("data") or []:
            mid = m.get("id")
            pricing = m.get("pricing") or {}
            if not mid:
                continue
            try:
                inp = float(pricing.get("prompt") or 0) * 1_000_000
                out = float(pricing.get("completion") or 0) * 1_000_000
            except (TypeError, ValueError):
                inp, out = 0.0, 0.0
            models[mid] = {"input_per_m": round(inp, 4), "output_per_m": round(out, 4)}
        _price_cache["at"] = now
        _price_cache["models"] = models
    except Exception:
        pass
    return models


def _resolve_pricing(key_def: dict[str, Any], live: dict[str, dict[str, float]]) -> dict[str, Any]:
    ref = key_def.get("pricing_ref")
    inp = key_def.get("static_input_per_m")
    out = key_def.get("static_output_per_m")
    source = "static"
    if ref and ref in live:
        inp = live[ref].get("input_per_m", inp)
        out = live[ref].get("output_per_m", out)
        source = "openrouter_live"
    score = None
    if inp is not None and out is not None:
        score = round(float(inp) * 0.7 + float(out) * 0.3, 4)
    return {
        "input_per_m": inp,
        "output_per_m": out,
        "cost_score": score,
        "pricing_source": source,
        "pricing_ref": ref,
    }


def compare_families(cfg: dict[str, Any]) -> dict[str, Any]:
    live = _fetch_openrouter_prices()
    cat = load_catalog(cfg)
    dev_root = Path(cfg.get("dev_root") or Path.home() / "dev")
    from fetch_usage import resolve_secret

    families: list[dict[str, Any]] = []

    for fam in cat.get("families") or []:
        if fam.get("id") in ("gateway", "dev_platform"):
            continue

        ranked: list[dict[str, Any]] = []
        for key_def in fam.get("keys") or []:
            if key_def.get("hidden"):
                continue
            env = key_def.get("env", "")
            pricing = _resolve_pricing(key_def, live)
            configured = bool(resolve_secret(env, dev_root))
            if pricing["cost_score"] is None and not key_def.get("notes"):
                continue
            ranked.append(
                {
                    "env": env,
                    "label": key_def.get("label", env),
                    "configured": configured,
                    "free_tier": key_def.get("free_tier", False),
                    **pricing,
                }
            )

        if not ranked:
            continue

        scored = [r for r in ranked if r.get("cost_score") is not None]
        scored.sort(key=lambda x: x["cost_score"])
        cheapest = scored[0] if scored else None
        configured_in_family = [r for r in ranked if r["configured"]]
        best_configured = min(configured_in_family, key=lambda x: x.get("cost_score") or 999) if configured_in_family else None

        savings = None
        if cheapest and best_configured and best_configured["env"] != cheapest["env"]:
            if best_configured.get("cost_score") and cheapest.get("cost_score"):
                savings = round(
                    (best_configured["cost_score"] - cheapest["cost_score"])
                    / best_configured["cost_score"]
                    * 100,
                    1,
                )

        missing = [r for r in ranked if not r["configured"]]
        missing.sort(key=lambda x: x.get("cost_score") or 999)

        families.append(
            {
                "id": fam.get("id"),
                "label": fam.get("label"),
                "purpose": fam.get("purpose"),
                "weight": fam.get("weight", 0.5),
                "repo_fit": fam.get("repo_fit") or [],
                "cheapest": cheapest,
                "best_configured": best_configured,
                "potential_savings_pct": savings,
                "ranked": scored[:8],
                "missing_cheapest": missing[:3],
                "configured_count": len(configured_in_family),
            }
        )

    families.sort(key=lambda f: (-f["weight"], f.get("potential_savings_pct") or 0), reverse=False)

    repo_projects = _load_repo_projects(cfg)
    gaps = _repo_gaps(families, repo_projects)

    return {
        "updated_at": int(time.time() * 1000),
        "pricing_live_source": "openrouter.ai/api/v1/models" if live else None,
        "families": families,
        "repo_gaps": gaps,
    }


def _load_repo_projects(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(cfg.get("modelrouter_root") or Path.home() / "dev" / "modelrouter")
    path = root / "config" / "projects.yaml"
    if not path.exists():
        return []
    try:
        import yaml

        data = yaml.safe_load(path.read_text()) or {}
        raw = data.get("projects") or {}
        if isinstance(raw, dict):
            return [{"id": k, **(v if isinstance(v, dict) else {})} for k, v in raw.items()]
        return raw if isinstance(raw, list) else []
    except Exception:
        return []


def _repo_gaps(families: list[dict[str, Any]], projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    project_ids = {
        (p.get("id") or p.get("name"))
        for p in projects
        if isinstance(p, dict)
    }

    for fam in families:
        repo_fit = set(fam.get("repo_fit") or [])
        if not repo_fit.intersection(project_ids):
            continue
        if fam.get("configured_count", 0) > 0:
            continue
        cheapest = fam.get("cheapest")
        gaps.append(
            {
                "family": fam.get("label"),
                "family_id": fam.get("id"),
                "purpose": fam.get("purpose"),
                "suggested": cheapest.get("label") if cheapest else None,
                "suggested_env": cheapest.get("env") if cheapest else None,
                "projects": sorted(repo_fit.intersection(project_ids)),
            }
        )
    return gaps

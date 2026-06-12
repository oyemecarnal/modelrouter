"""Assess my APIs — structured comparison + optional ModelRouter LLM narrative."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from api_catalog import catalog_with_status
from api_comparator import compare_families
from fetch_usage import load_config, parse_env_file, resolve_secret


def _repo_context(cfg: dict[str, Any]) -> dict[str, Any]:
    root = Path(cfg.get("modelrouter_root") or Path.home() / "dev" / "modelrouter")
    ctx: dict[str, Any] = {"projects": [], "presets": [], "cost_alternatives": []}

    try:
        import yaml

        projects_path = root / "config" / "projects.yaml"
        if projects_path.exists():
            pdata = yaml.safe_load(projects_path.read_text()) or {}
            raw = pdata.get("projects") or {}
            if isinstance(raw, dict):
                items = [{"id": k, **(v if isinstance(v, dict) else {})} for k, v in raw.items()]
            else:
                items = raw if isinstance(raw, list) else []
            ctx["projects"] = [
                {
                    "id": p.get("id"),
                    "presets": p.get("presets"),
                    "description": p.get("description"),
                }
                for p in items[:12]
            ]
        presets_path = root / "config" / "includes" / "policy_presets.yaml"
        if presets_path.exists():
            pdata = yaml.safe_load(presets_path.read_text()) or {}
            ctx["presets"] = list((pdata.get("preset_models") or {}).keys())[:12]
        cost_path = root / "config" / "cost_alternatives.yaml"
        if cost_path.exists():
            cdata = yaml.safe_load(cost_path.read_text()) or {}
            ctx["cost_alternatives"] = [
                a.get("use") for a in (cdata.get("alternatives") or [])[:8] if a.get("use")
            ]
    except Exception:
        pass
    return ctx


def build_assessment_payload(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    catalog = catalog_with_status(cfg)
    comparison = compare_families(cfg)
    repo = _repo_context(cfg)

    return {
        "catalog_summary": catalog.get("summary"),
        "families": [
            {
                "id": f["id"],
                "label": f["label"],
                "coverage": f.get("coverage"),
                "configured": f.get("configured_count"),
                "keys": [
                    {"label": k["label"], "status": k["status"], "free_tier": k.get("free_tier")}
                    for k in f.get("keys", [])
                ],
            }
            for f in catalog.get("families", [])
        ],
        "comparison": [
            {
                "family": c["label"],
                "cheapest": c.get("cheapest", {}).get("label") if c.get("cheapest") else None,
                "cheapest_cost_score": c.get("cheapest", {}).get("cost_score") if c.get("cheapest") else None,
                "your_best": c.get("best_configured", {}).get("label") if c.get("best_configured") else None,
                "savings_pct": c.get("potential_savings_pct"),
                "missing_cheapest": [m["label"] for m in c.get("missing_cheapest", [])],
            }
            for c in comparison.get("families", [])
        ],
        "repo_gaps": comparison.get("repo_gaps", []),
        "repo": repo,
    }


def _gateway_config(cfg: dict[str, Any]) -> tuple[str, str, str]:
    root = Path(cfg.get("modelrouter_root") or Path.home() / "dev" / "modelrouter")
    env = parse_env_file(root / ".env")
    host = env.get("MODELROUTER_HOST") or os.environ.get("MODELROUTER_HOST") or "127.0.0.1"
    port = env.get("MODELROUTER_PORT") or os.environ.get("MODELROUTER_PORT") or "3000"
    key = resolve_secret("MODELROUTER_MASTER_KEY", Path(cfg.get("dev_root") or Path.home() / "dev"))
    model = (cfg.get("assess") or {}).get("model") or "fast"
    return f"http://{host}:{port}", key or "", model


def _llm_narrative(payload: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    base, api_key, model = _gateway_config(cfg)
    if not api_key:
        return {"status": "unavailable", "error": "MODELROUTER_MASTER_KEY not set", "text": None}

    system = (
        "You are ModelRouter's API cost advisor. Given JSON inventory and pricing comparison, "
        "write a concise assessment: (1) coverage by family, (2) cost winners per class with $/1M "
        "token hints where present, (3) gaps for this homelab's projects, (4) pros/cons of switching, "
        "(5) what NOT to add (redundant). No secrets. Markdown bullets. Under 400 words."
    )
    user = json.dumps(payload, indent=2)[:12000]

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 900,
    }

    req = urllib.request.Request(
        f"{base}/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        return {"status": "ok", "model": model, "text": text.strip()}
    except urllib.error.HTTPError as exc:
        err = exc.read().decode()[:300]
        return {"status": "error", "error": f"HTTP {exc.code}: {err}", "text": None}
    except Exception as exc:
        return {"status": "error", "error": str(exc)[:200], "text": None}


def assess_apis(cfg: dict[str, Any] | None = None, *, use_llm: bool = True) -> dict[str, Any]:
    cfg = cfg or load_config()
    payload = build_assessment_payload(cfg)
    result: dict[str, Any] = {
        "updated_at": payload.get("catalog_summary"),
        "structured": payload,
        "narrative": None,
    }
    comparison = compare_families(cfg)
    result["comparison"] = comparison
    result["catalog"] = catalog_with_status(cfg)

    if use_llm and (cfg.get("assess") or {}).get("enabled", True):
        result["narrative"] = _llm_narrative(payload, cfg)

    result["updated_at"] = comparison.get("updated_at")
    return result


def rule_based_summary(payload: dict[str, Any]) -> str:
    """Fallback when gateway offline."""
    lines = ["## API assessment (offline)", ""]
    summary = payload.get("catalog_summary") or {}
    lines.append(
        f"- **Configured:** {summary.get('keys_configured', 0)} / {summary.get('keys_tracked', 0)} tracked keys"
    )
    for row in payload.get("comparison") or []:
        if row.get("savings_pct"):
            lines.append(
                f"- **{row['family']}:** consider {row.get('missing_cheapest', ['?'])[0]} "
                f"(~{row['savings_pct']}% cheaper than your current pick)"
            )
    for gap in payload.get("repo_gaps") or []:
        lines.append(f"- **Gap for {', '.join(gap.get('projects', []))}:** add {gap.get('suggested')} ({gap.get('family')})")
    return "\n".join(lines)

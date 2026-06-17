"""
Route recommendations — closes the loop between the keys widget and routing presets.

Reads TokenWidget snapshot (quota pressure) and suggests which preset to use.
Agents (Hermes, etc.) or MCP can call `recommend()` before picking a model.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = Path.home() / "Library/Application Support/TokenWidget/snapshot.json"
HINTS_PATH = ROOT / "data" / "route_hints.json"
PROJECTS_PATH = ROOT / "config" / "projects.yaml"


@dataclass
class RouteRecommendation:
    project: str
    preset: str
    reason: str
    pressure: dict[str, float]
    updated_at: int
    key_hints: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_PRESSURE_KEY_HINTS: tuple[tuple[str, str], ...] = (
    ("groq", "GROQ_API_KEY"),
    ("openai-codex", "OPENAI_API_KEY"),
    ("gpt-4o", "OPENAI_API_KEY"),
    ("mistral", "MISTRAL_API_KEY"),
)


def _vault_key_hints(preset: str, pressure: dict[str, float]) -> dict[str, str]:
    """When quota pressure is high and alternates exist, suggest vault key fingerprints."""
    try:
        from modelrouter.key_vault import load_vault, load_vault_config, select_key

        cfg = load_vault_config()
        route = (cfg.get("routing") or {}).get(preset) or {}
        prefer = set(route.get("prefer") or [])
        doc = load_vault(cfg)
    except (FileNotFoundError, OSError, ImportError):
        return {}

    hints: dict[str, str] = {}
    seen_env: set[str] = set()
    for pid, env_var in _PRESSURE_KEY_HINTS:
        if env_var in seen_env:
            continue
        if prefer and env_var not in prefer:
            continue
        if float(pressure.get(pid, 0)) < 76:
            continue
        enabled = [r for r in doc.get("keys") or [] if r.get("env_var") == env_var and r.get("enabled", True)]
        if len(enabled) < 2:
            continue
        chosen = select_key(env_var, preset=preset, cfg=cfg, mark_used=False)
        if chosen:
            hints[env_var] = chosen.fingerprint
            seen_env.add(env_var)
    return hints


def _load_snapshot() -> dict[str, Any]:
    if not SNAPSHOT.exists():
        return {}
    try:
        return json.loads(SNAPSHOT.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _provider_pressure(snapshot: dict[str, Any]) -> dict[str, float]:
    """0 = plenty of quota left, 100 = exhausted."""
    pressure: dict[str, float] = {}
    for p in snapshot.get("providers") or []:
        if p.get("kind") == "configured":
            continue
        pid = p.get("id") or ""
        for w in p.get("windows") or []:
            used = float(w.get("used_percent") or 0)
            remaining = w.get("remaining_percent")
            if remaining is not None:
                used = max(used, 100.0 - float(remaining))
            if used:
                pressure[pid] = max(pressure.get(pid, 0.0), used)
    return pressure


def recommend(
    project: str = "smalshi-hermes",
    *,
    complex_task: bool = False,
    offline_ok: bool = False,
    write_hints: bool = True,
) -> RouteRecommendation:
    import yaml

    projects: dict = {}
    if PROJECTS_PATH.exists():
        projects = yaml.safe_load(PROJECTS_PATH.read_text()) or {}
    proj = (projects.get("projects") or {}).get(project) or {}
    presets = proj.get("presets") or {}

    snap = _load_snapshot()
    pressure = _provider_pressure(snap)

    openai_hot = max(pressure.get("openai-codex", 0), pressure.get("gpt-4o", 0))
    groq_ok = pressure.get("groq", 0) < 80
    mistral_ok = pressure.get("mistral", 0) < 80

    if offline_ok:
        preset = presets.get("offline", "offline")
        reason = "Offline-preferred mode"
    elif complex_task:
        preset = presets.get("complex") or presets.get("analysis") or presets.get("default") or "hermes-smart"
        if openai_hot > 70 and groq_ok:
            preset = "code"
            reason = "OpenAI/Codex quota hot — using code preset (Groq-first)"
        else:
            reason = "Complex / high-stakes task"
    else:
        preset = presets.get("routine") or presets.get("tab") or presets.get("default") or "hermes-fast"
        if openai_hot > 60:
            preset = "cheap" if preset.startswith("hermes") else "groq-fast"
            reason = f"OpenAI pressure {openai_hot:.0f}% — downshifted to {preset}"
        elif not groq_ok and mistral_ok:
            preset = "mistral-small"
            reason = "Groq pressure high — preferring Mistral"
        else:
            reason = "Routine / low-risk task"

    rec = RouteRecommendation(
        project=project,
        preset=preset,
        reason=reason,
        pressure=pressure,
        updated_at=int(time.time() * 1000),
        key_hints=_vault_key_hints(preset, pressure),
    )
    if write_hints:
        HINTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        HINTS_PATH.write_text(json.dumps(rec.to_dict(), indent=2) + "\n")
    return rec


def all_project_hints(*, complex_task: bool = False) -> dict[str, dict[str, Any]]:
    import yaml

    projects = (yaml.safe_load(PROJECTS_PATH.read_text()) or {}).get("projects") or {}
    out: dict[str, dict[str, Any]] = {}
    for name in projects:
        rec = recommend(name, complex_task=complex_task, write_hints=False)
        out[name] = {k: v for k, v in rec.to_dict().items()}
    HINTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    HINTS_PATH.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ModelRouter route recommendation")
    parser.add_argument("--project", default="smalshi-hermes")
    parser.add_argument("--complex", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all:
        print(json.dumps(all_project_hints(complex_task=args.complex), indent=2))
    else:
        print(json.dumps(recommend(args.project, complex_task=args.complex, offline_ok=args.offline).to_dict(), indent=2))

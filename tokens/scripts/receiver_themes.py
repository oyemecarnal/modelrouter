"""Stereo receiver color presets — infinite override via tokens/config.json receiver.led."""

from __future__ import annotations

from typing import Any

# id → theme dict (background, panel, bezel, label, led{ok,warn,down,skip,off})
THEME_PRESETS: dict[str, dict[str, Any]] = {
    "classic-rg": {
        "name": "Classic R/G",
        "hint": "Red chassis · green on · red off",
        "background": "#1a0505",
        "panel": "#2a0808",
        "bezel": "#5c1818",
        "label": "#e8a0a0",
        "led": {
            "ok": "#00ff55",
            "warn": "#cc8800",
            "down": "#4a1010",
            "skip": "#2a0808",
            "off": "#4a1010",
        },
    },
    "marantz": {
        "name": "Marantz",
        "hint": "Warm amber · bronze face",
        "background": "#14100a",
        "panel": "#1f1810",
        "bezel": "#6b4a28",
        "label": "#d4a574",
        "led": {
            "ok": "#ffb347",
            "warn": "#ff6b1a",
            "down": "#8b2500",
            "skip": "#3d2e1a",
            "off": "#1a1208",
        },
    },
    "mcintosh": {
        "name": "McIntosh",
        "hint": "Blue meters · black glass",
        "background": "#050608",
        "panel": "#0c1018",
        "bezel": "#1e3a5f",
        "label": "#7eb8e8",
        "led": {
            "ok": "#4de8ff",
            "warn": "#ffd966",
            "down": "#ff4466",
            "skip": "#1a2838",
            "off": "#080c12",
        },
    },
    "denon": {
        "name": "Denon",
        "hint": "Cool silver · ice white LEDs",
        "background": "#0e1014",
        "panel": "#181c24",
        "bezel": "#6a7280",
        "label": "#b8c0cc",
        "led": {
            "ok": "#e8f4ff",
            "warn": "#7eb8ff",
            "down": "#ff5566",
            "skip": "#2a3040",
            "off": "#10141c",
        },
    },
    "pioneer": {
        "name": "Pioneer",
        "hint": "Charcoal · cyan accent",
        "background": "#0a0c10",
        "panel": "#141820",
        "bezel": "#2a3548",
        "label": "#88a8c8",
        "led": {
            "ok": "#00e5cc",
            "warn": "#ffaa00",
            "down": "#ff3355",
            "skip": "#1e2838",
            "off": "#0c1018",
        },
    },
}


def preset_ids() -> list[str]:
    return list(THEME_PRESETS.keys())


def get_preset(preset_id: str) -> dict[str, Any] | None:
    return THEME_PRESETS.get(preset_id)


def merge_custom(preset_id: str, cfg_receiver: dict[str, Any]) -> dict[str, Any]:
    """Apply config.json receiver overrides on top of a preset (infinite choice)."""
    base = dict(THEME_PRESETS.get(preset_id) or THEME_PRESETS["classic-rg"])
    led = {**base.get("led", {}), **(cfg_receiver.get("led") or {})}
    for key in ("background", "panel", "bezel", "label"):
        if cfg_receiver.get(key):
            base[key] = cfg_receiver[key]
    base["led"] = led
    return base


def presets_for_snapshot(cfg: dict[str, Any]) -> dict[str, Any]:
    rx = cfg.get("receiver") or {}
    default = rx.get("default_preset") or "classic-rg"
    out: dict[str, Any] = {}
    for pid, preset in THEME_PRESETS.items():
        out[pid] = {
            "name": preset["name"],
            "hint": preset.get("hint", ""),
            **{k: preset[k] for k in ("background", "panel", "bezel", "label") if k in preset},
            "led": dict(preset.get("led") or {}),
        }
    return {"defaultPreset": default, "presets": out}

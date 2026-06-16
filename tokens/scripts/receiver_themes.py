"""Stereo receiver color presets — infinite override via tokens/config.json receiver.led."""

from __future__ import annotations

from typing import Any

# id → theme dict (background, panel, bezel, label, led{ok,warn,down,skip,off}, category, hint)
THEME_PRESETS: dict[str, dict[str, Any]] = {
    "classic-rg": {
        "name": "Classic R/G",
        "category": "Receivers",
        "hint": "1970s red chassis · green power LED",
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
        "category": "Receivers",
        "hint": "Warm amber · bronze faceplate",
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
        "category": "Receivers",
        "hint": "Blue watt meters · black glass",
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
        "category": "Receivers",
        "hint": "Cool silver · ice-white pilots",
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
        "category": "Receivers",
        "hint": "Charcoal SX · cyan accent",
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
    "tube-warm": {
        "name": "Tube Amp",
        "category": "Tube / analog",
        "hint": "Tolex & filament glow · slow pulse",
        "background": "#1a0f08",
        "panel": "#261810",
        "bezel": "#5c3820",
        "label": "#e8b896",
        "led": {
            "ok": "#ff9933",
            "warn": "#ffcc66",
            "down": "#662200",
            "skip": "#2a1810",
            "off": "#1a1008",
        },
        "fx": "tube-pulse",
    },
    "tek-scope": {
        "name": "Tek Scope",
        "category": "Lab / test",
        "hint": "465 CRT · green phosphor trace",
        "background": "#0a1208",
        "panel": "#0f1a0c",
        "bezel": "#1a4020",
        "label": "#88ffaa",
        "led": {
            "ok": "#33ff66",
            "warn": "#aaff33",
            "down": "#ff4444",
            "skip": "#142818",
            "off": "#081008",
        },
        "fx": "phosphor",
    },
    "luxman": {
        "name": "Luxman",
        "category": "Receivers",
        "hint": "Gold face · dark lacquer wood",
        "background": "#120e06",
        "panel": "#1a1408",
        "bezel": "#8b6914",
        "label": "#d4af37",
        "led": {
            "ok": "#ffd700",
            "warn": "#ff8c00",
            "down": "#8b0000",
            "skip": "#2a2010",
            "off": "#140f06",
        },
    },
    "nakamichi": {
        "name": "Nakamichi",
        "category": "Receivers",
        "hint": "1980s champagne silver · cool blue",
        "background": "#121418",
        "panel": "#1c2028",
        "bezel": "#8899aa",
        "label": "#c8d4e0",
        "led": {
            "ok": "#a8d8ff",
            "warn": "#ffb366",
            "down": "#ff5566",
            "skip": "#242830",
            "off": "#101418",
        },
    },
    "fuse-panel": {
        "name": "Fuse Panel",
        "category": "Industrial",
        "hint": "Rack PDU · amber pilots · square bezels",
        "background": "#0c0c0e",
        "panel": "#161618",
        "bezel": "#444448",
        "label": "#909098",
        "led": {
            "ok": "#ffcc00",
            "warn": "#ff8800",
            "down": "#ff2222",
            "skip": "#2a2a30",
            "off": "#18181c",
        },
        "fx": "fuse-bezel",
    },
    "vintage-radio": {
        "name": "Vintage Radio",
        "category": "Tube / analog",
        "hint": "Zenith dial · cream & tuning glow",
        "background": "#1a1210",
        "panel": "#281816",
        "bezel": "#6b4030",
        "label": "#f0c8a0",
        "led": {
            "ok": "#ff6644",
            "warn": "#ffaa44",
            "down": "#881818",
            "skip": "#302018",
            "off": "#181008",
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
    for key in ("background", "panel", "bezel", "label", "fx"):
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
            "category": preset.get("category", "Receivers"),
            "fx": preset.get("fx", ""),
            **{k: preset[k] for k in ("background", "panel", "bezel", "label") if k in preset},
            "led": dict(preset.get("led") or {}),
        }
    return {"defaultPreset": default, "presets": out}

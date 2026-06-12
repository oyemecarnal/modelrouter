#!/usr/bin/env python3
"""ModelRouter MCP server — health, models, route recommendations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent.parent


def _base() -> str:
    host = os.environ.get("MODELROUTER_HOST", "127.0.0.1")
    port = os.environ.get("MODELROUTER_PORT", "3000")
    return f"http://{host}:{port}"


def _key() -> str:
    if os.environ.get("MODELROUTER_MASTER_KEY"):
        return os.environ["MODELROUTER_MASTER_KEY"]
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("MODELROUTER_MASTER_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return "sk-modelrouter-change-me"


def _get(path: str) -> dict[str, Any]:
    r = httpx.get(f"{_base()}{path}", headers={"Authorization": f"Bearer {_key()}"}, timeout=15)
    r.raise_for_status()
    return r.json()


def create_app():
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("modelrouter")

    @mcp.tool()
    def health() -> str:
        """Check if ModelRouter proxy is alive."""
        try:
            r = httpx.get(f"{_base()}/health/liveliness", timeout=5)
            return r.text if r.status_code == 200 else f"down ({r.status_code})"
        except Exception as exc:
            return f"down: {exc}"

    @mcp.tool()
    def list_models() -> str:
        """List available model aliases including policy presets."""
        data = _get("/v1/models")
        ids = sorted(m["id"] for m in data.get("data", []))
        presets = [i for i in ids if i in {
            "smart", "fast", "cheap", "code", "review", "local", "offline",
            "hermes-fast", "hermes-smart", "groq-llama", "mistral-small",
        }]
        return json.dumps({"presets": presets, "total": len(ids), "all": ids[:40]}, indent=2)

    @mcp.tool()
    def route_recommend(project: str = "smalshi-hermes", complex_task: bool = False) -> str:
        """Recommend a model preset using widget quota + project config (closes the loop)."""
        from modelrouter.route_policy import recommend

        return json.dumps(
            recommend(project, complex_task=complex_task).to_dict(),
            indent=2,
        )

    @mcp.tool()
    def project_presets() -> str:
        """Show per-project preset mapping from config/projects.yaml."""
        import yaml

        path = ROOT / "config" / "projects.yaml"
        return path.read_text() if path.exists() else "{}"

    return mcp


def main() -> None:
    create_app().run()


if __name__ == "__main__":
    main()

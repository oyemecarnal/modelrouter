# Development Agents

Curated prompts from [agency-agents](https://github.com/msitarzewski/agency-agents) (on `kc-mini` at `~/dev/agency_agents/`) for building and operating ModelRouter.

These are **not runtime code** — they're specialist personas you invoke in Cursor when working on this repo.

| Agent | Use for ModelRouter |
|-------|---------------------|
| `engineering-sre.md` | SLOs, health checks, launchd/Docker reliability, incident playbooks |
| `engineering-devops-automator.md` | CI/CD, Docker Compose, deploy-to-mini automation |
| `engineering-incident-response-commander.md` | Outages, provider failures, circuit breaker triage |
| `engineering-backend-architect.md` | API design, routing config, LiteLLM proxy architecture |
| `engineering-ai-engineer.md` | Model selection, fallbacks, prompt/tool routing |
| `engineering-software-architect.md` | System design, plugin boundaries, extension points |
| `specialized-mcp-builder.md` | Exposing ModelRouter via MCP for Cursor/agents |

## Usage in Cursor

```
@engineering-sre Review ModelRouter health checks and launchd setup for 99.9% uptime.
@engineering-backend-architect Design fallbacks for smart → fast → local routing.
@specialized-mcp-builder Add an MCP server that wraps ModelRouter /v1/models and /health.
```

## Install more agents from Mac mini

```bash
./scripts/install-dev-agents.sh          # refresh curated set from kc-mini
./scripts/install-dev-agents.sh --all    # install full agency-agents to ~/.cursor via upstream installer
```

## Memory-powered workflows

See `docs/DEVELOPMENT.md` for multi-agent handoff patterns using MCP memory (from agency-agents `workflow-with-memory`).

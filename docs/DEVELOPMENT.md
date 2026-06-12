# Developing ModelRouter

## Stack

- **LiteLLM proxy** — multi-provider routing, fallbacks, rate limits
- **config/modelrouter.yaml** — production config (Redis + all providers)
- **config/modelrouter.minimal.yaml** — local dev without Redis/Postgres
- **scripts/** — secrets, start/stop, deploy
- **modelrouter/** — Python callbacks (logging, future plugins)

## Agency-agents workflow

ModelRouter borrows development patterns from `agency-agents` on the Mac mini (`~/dev/agency_agents/`). That repo is a library of specialist agent prompts — not executable routing code — but highly useful for building and operating this gateway.

### Recommended agents (in `agents/`)

1. **Backend Architect** — config schema, API compatibility with OpenRouter
2. **SRE** — always-on reliability on `kc-mini`, SLOs for `/health` and chat latency
3. **DevOps Automator** — Docker Compose, `deploy-to-mini.sh`, launchd
4. **Incident Response Commander** — when a provider or circuit breaker trips
5. **MCP Builder** — expose ModelRouter to Cursor via MCP

### Example session

```
@engineering-backend-architect
Add Anthropic native routing to config/modelrouter.yaml with fallbacks to OpenAI.

@engineering-sre
Define SLOs for ModelRouter: p99 latency < 30s, availability 99.5%, error budget alerts.

@specialized-mcp-builder
Create an MCP tool that lists models and checks /health on the local gateway.
```

### Memory integration (optional)

If you use an MCP memory server (see agency-agents `integrations/mcp-memory/`), tag memories with `modelrouter` so agents recall prior config decisions across sessions.

## Always-on deployment (kc-mini)

```bash
# From your MacBook
./scripts/deploy-to-mini.sh

# On kc-mini (or via SSH)
make daemon-enable   # launchd auto-start
make health
```

## Local development

```bash
make install
make daemon
make health
make logs
```

## Adding features later

Register custom LiteLLM callbacks in `modelrouter/` and add to config:

```yaml
litellm_settings:
  success_callback: ["modelrouter.logging_callback.logging_callback"]
```

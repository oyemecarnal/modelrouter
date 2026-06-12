# ModelRouter

Self-hosted LLM gateway powered by **[LiteLLM](https://docs.litellm.ai/)**. One OpenAI-compatible endpoint for OpenAI, Anthropic, Gemini, Ollama, and 100+ providers — with fallbacks, circuit breakers, caching, and 1Password secrets.

Drop-in replacement for OpenRouter on your machine.

```
Base URL: http://127.0.0.1:3000
API Key:  <MODELROUTER_MASTER_KEY>
```

## Quick start

```bash
make install          # venv + litellm + config files
cp .env.example .env  # add your keys (or use secrets.yaml + 1Password)
make daemon           # start in background
make health           # verify it's up
```

Test:

```bash
curl http://127.0.0.1:3000/v1/models \
  -H "Authorization: Bearer $MODELROUTER_MASTER_KEY"

curl http://127.0.0.1:3000/v1/chat/completions \
  -H "Authorization: Bearer $MODELROUTER_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"smart","messages":[{"role":"user","content":"Hello"}]}'
```

Use with Cursor / Continue / any OpenAI client — set base URL to `http://127.0.0.1:3000`.

## Architecture

```
Client (Cursor, etc.)
        │
        ▼
┌───────────────────┐
│   ModelRouter     │  ← LiteLLM proxy + custom callbacks
│   :3000           │
└────────┬──────────┘
         │
    ┌────┴────┬──────────┬─────────┐
    ▼         ▼          ▼         ▼
 OpenAI   Anthropic   Gemini    Ollama
```

**Production stack** (Docker):

```
Client → ModelRouter (LiteLLM) → Redis (cache/rate limits)
                               → Postgres (keys, spend tracking)
                               → Providers
```

## 1Password integration

```bash
brew install 1password-cli
op signin
cp secrets.example.yaml secrets.yaml
# Edit op:// references to match your vault
```

Secrets load automatically at startup via `scripts/load_secrets.py`. Priority:

1. Already-set environment variables (never overwritten)
2. 1Password `op read` references from `secrets.yaml`
3. `.env` file values

## Model aliases

| Alias | Routes to |
|-------|-----------|
| `smart` | gpt-4o → claude-sonnet (load balanced) |
| `fast` | gpt-4o-mini → gemini-flash |
| `local` | Ollama llama3.2 / qwen2.5 |
| `embedding` | text-embedding-3-small |

Fallbacks: `smart` → `fast` → `local` (configured in `config/modelrouter.yaml`).

## Configuration

| File | Purpose |
|------|---------|
| `config/modelrouter.yaml` | Full config (Redis cache, all providers) |
| `config/modelrouter.minimal.yaml` | No Redis/DB required (auto-selected) |
| `config/modelrouter.local.yaml` | Your overrides (gitignored) |
| `secrets.yaml` | 1Password references (gitignored) |
| `.env` | Plain env vars |

Start script auto-selects config:
- Redis available → full config with caching
- No Redis → minimal config (still has fallbacks + retries)

## Operations

```bash
make start            # foreground
make daemon           # background
make stop             # stop daemon
make restart          # stop + daemon
make health           # health check
make logs             # tail logs
make status           # health + PID

# Auto-start at login (macOS launchd)
make daemon-enable
make daemon-disable
```

## Docker (production)

```bash
cp .env.example .env   # set MODELROUTER_MASTER_KEY + provider keys
docker compose up -d
docker compose logs -f modelrouter
```

Includes Postgres (virtual keys, spend tracking) and Redis (shared cache).

## Hardening checklist

- [x] Master key auth (`MODELROUTER_MASTER_KEY`, must start with `sk-`)
- [x] Bind to localhost only (`127.0.0.1`)
- [x] Rate limits per model (`rpm` in config)
- [x] Circuit breaker (`allowed_fails`, `cooldown_time`)
- [x] Model fallbacks
- [x] Structured JSON logging
- [x] Health checks + auto-restart (launchd / Docker `restart: unless-stopped`)
- [x] Secrets via 1Password (no keys in config files)
- [x] `drop_params` — strips unsupported params per provider
- [ ] Set strong `LITELLM_SALT_KEY` for production DB
- [ ] TLS termination (nginx/caddy in front)

## Custom extensions

ModelRouter hooks into LiteLLM via `modelrouter/logging_callback.py`. Add more callbacks or plugins in the `modelrouter/` package and register in config:

```yaml
litellm_settings:
  success_callback: ["modelrouter.logging_callback.logging_callback"]
```

## Environment variables

| Variable | Description |
|----------|-------------|
| `MODELROUTER_MASTER_KEY` | Client API key |
| `MODELROUTER_PORT` | Port (default `3000`) |
| `MODELROUTER_HOST` | Bind address (default `127.0.0.1`) |
| `OPENAI_API_KEY` | OpenAI provider key |
| `ANTHROPIC_API_KEY` | Anthropic provider key |
| `GOOGLE_API_KEY` | Google Gemini key |
| `OLLAMA_API_BASE` | Ollama URL (default `http://127.0.0.1:11434`) |
| `REDIS_HOST` / `REDIS_PORT` | Redis for caching |
| `DATABASE_URL` | Postgres (Docker stack) |
| `OP_ACCOUNT` | 1Password account shorthand |

## Agency-agents integration

The Mac mini has `~/dev/agency_agents/agency-agents-main.zip` — a library of specialist **agent prompts** (not routing code). We pulled in the pieces useful for building and operating ModelRouter:

| Borrowed | Purpose |
|----------|---------|
| `agents/*.md` | SRE, DevOps, Backend Architect, MCP Builder personas for development |
| `scripts/install-dev-agents.sh` | Refresh agents from `kc-mini` |
| `scripts/deploy-to-mini.sh` | Sync + start on always-on Mac mini |
| `.cursor/rules/modelrouter.mdc` | Project context for Cursor |
| `docs/DEVELOPMENT.md` | Multi-agent workflow patterns (memory handoffs) |

```bash
make agents        # sync curated agents from kc-mini
make deploy-mini   # deploy to Mac mini and start daemon
```

## Keys widget

Square desktop panel for live API usage and masked key inventory (`tokens/` — ingested from Mac mini `~/dev/tokens`):

```bash
make keys-widget-install   # venv + background refresh
make keys-widget           # open panel (Refresh + Edit buttons)
```

See `tokens/README.md` for provider details.

## Roadmap

- [x] Local keys widget (usage + inventory)
- [ ] Virtual key management UI (LiteLLM Admin UI)
- [ ] Cost tracking dashboard
- [ ] 1Password Connect Server (no CLI)
- [ ] Custom auth middleware
- [ ] Prometheus metrics

## License

MIT

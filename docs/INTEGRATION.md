# Integrate ModelRouter with any repo

ModelRouter is an **OpenAI-compatible gateway**. Any client that accepts `OPENAI_API_BASE` + `OPENAI_API_KEY` can use policy **presets** instead of vendor model names.

## Solo laptop (5 minutes)

```bash
git clone https://github.com/oyemecarnal/modelrouter.git ~/dev/modelrouter
cd ~/dev/modelrouter
make install
cp .env.example .env          # add provider keys
make daemon && make health
```

In **your app repo**:

```bash
cp ~/dev/modelrouter/templates/repo.env.modelrouter .env.modelrouter
# Edit OPENAI_API_KEY → your MODELROUTER_MASTER_KEY from modelrouter/.env
source .env.modelrouter
```

Call the API with a **preset** as the model:

```bash
curl http://127.0.0.1:3000/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"cheap","messages":[{"role":"user","content":"Hello"}]}'
```

Presets: `cheap`, `fast`, `smart`, `code`, `hermes-fast`, `hermes-smart`, `review`, `offline` — see `config/includes/policy_presets.yaml`.

## Register your project (optional)

Track routing hints and virtual key names in ModelRouter:

```bash
cd ~/dev/modelrouter
make register-project PROJECT=my-bot ROUTINE=hermes-fast COMPLEX=hermes-smart
make issue-project-keys    # writes MODELROUTER_KEY_MY_BOT in .env (native mode = master key)
```

Or:

```bash
./scripts/register-project.sh my-bot --host laptop --routine cheap --complex smart
```

## Homelab (agents on another machine)

1. Gateway on always-on host — `make deploy-mini` or run locally
2. Copy `config/hosts.local.yaml.example` → `config/hosts.local.yaml`
3. Runtime host gets **gateway auth only**:

```bash
make push-client-env-tower   # or copy config/client.env.example
```

No `GROQ_API_KEY`, `ANTHROPIC_API_KEY`, etc. on runtime hosts.

## Cursor / Continue

Base URL: `http://127.0.0.1:3000/v1` (laptop) or your LAN gateway URL.  
API key: `MODELROUTER_MASTER_KEY` from `.env`.  
See `docs/CURSOR_WIRING.md`.

## Python agents

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:3000/v1",
    api_key=os.environ["OPENAI_API_KEY"],
)
client.chat.completions.create(model="hermes-fast", messages=[...])
```

## Route hints (optional)

Before picking a preset, agents can ask ModelRouter for pressure-aware advice:

```bash
PYTHONPATH=. .venv/bin/python -m modelrouter.route_policy --project my-bot
```

## MCP (Cursor agents)

```bash
make mcp-install   # copies .cursor/mcp.json.example → .cursor/mcp.json
```

## Key rotation

Provider keys live in **modelrouter** `.env` only. On 429, the gateway can rotate via key vault — see `docs/KEY_VAULT.md`. Clients do not need to change.

## Related

- `docs/HOSTS.md` — multi-machine URLs
- `docs/CLEAN_WIRES.md` — one meter, no stray provider keys
- `config/projects.yaml` — project → preset mapping SSOT

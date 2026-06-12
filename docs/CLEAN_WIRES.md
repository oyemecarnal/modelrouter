# Clean wires — separation manifesto

Before calibrating tokens, context windows, or cross-machine routing, **every client must use one untangled path into ModelRouter**.

## The problem today

Wires are crossed when:

- Cursor, Hermes, and bots each carry **their own** provider keys
- The same key lives in `.env`, `.zshrc`, `smalshi/.env`, and `tokens/.env.local`
- Apps call OpenAI/Groq **directly** and **via** ModelRouter
- `CURSOR_API_KEY` (Cursor’s product) is confused with `MODELROUTER_MASTER_KEY` (your gateway)

You cannot calibrate spend or context until traffic flows through **one meter**.

## Target topology

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Cursor    │  │   Hermes    │  │ Kalshi/coin │
│  (laptop)   │  │  (tower)    │  │  (tower)    │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │ project key     │ project key     │
       │ preset          │ preset          │
       └────────────────┼─────────────────┘
                        ▼
              ┌──────────────────┐
              │   ModelRouter    │  ← single API surface
              │   /v1/*          │     MODELROUTER_MASTER_KEY
              │   kc-mini:3000   │     + per-project virtual keys
              └────────┬─────────┘
                       │ provider keys ONLY here
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
      OpenAI        Groq/Mistral    Ollama
```

**No provider keys on tower.** No direct vendor calls from agents except through ModelRouter (or an explicit documented exception in `config/projects.yaml`).

## Namespace rules

| Prefix | Owner | Purpose |
|--------|--------|---------|
| `MODELROUTER_*` | Gateway | Master key, port, host, salt |
| `MODELROUTER_KEY_*` | Per-project client auth | Hermes, Kalshi, Cursor labels |
| Provider `*_API_KEY` | **kc-mini `.env` only** | OpenAI, Groq, etc. |
| `CURSOR_API_KEY` | Cursor product / widget | **Not** the gateway key |

## Migration checklist (homelab)

- [ ] Cursor: base URL → ModelRouter; API key → `MODELROUTER_MASTER_KEY` only
- [ ] Hermes/tower: `OPENAI_BASE_URL=http://Kevins-Mac-mini.local:3000/v1`, model = preset name
- [ ] Remove provider keys from tower `.env` files (keep Polygon etc. where data APIs run)
- [ ] Stop new keys in `~/.zshrc` — mini `modelrouter/.env` + 1Password
- [ ] `make keys-audit` monthly; `make cost-review` each cycle
- [ ] Document exceptions in `config/projects.yaml` if something must bypass gateway

## Inventory harness

Know what's on disk before consolidating:

```bash
make inventory       # masked API + crypto surfaces (allowed paths only)
make inventory-mini  # same on kc-mini
```

See `docs/INVENTORY.md` — wallet-*style* audit (locations, not custody).

## Calibration (only after clean wires)

Once traffic is metered:

1. **Tokens** — LiteLLM logs + future UI show per-project / per-preset usage
2. **Context windows** — map presets to max context in `config/models_catalog.yaml` (future)
3. **Cross-machine** — same presets on laptop, mini, tower; gateway is source of truth

## What not to tangle

| Keep separate | Why |
|---------------|-----|
| `tokens/` widget | Read-only quota display; not the gateway |
| LiteLLM Admin UI | Future; optional Docker stack |
| Provider dashboards | Login via “Add provider” in future UI; keys land in vault only |

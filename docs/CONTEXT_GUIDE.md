# Context window guide

**SSOT:** `config/models_catalog.yaml` — every provider model has `context_window`.  
**Enforcement:** `make check-catalog` fails if any catalog model is missing it.

Use this when choosing a **preset** (not a raw vendor model). Clients should call presets; the gateway maps them to provider models.

## Quick picks

| Situation | Preset | Why |
|-----------|--------|-----|
| Short Q&A, bot loops, high volume | `cheap` | 4k output cap; Groq free tier; 131k context on primary model |
| Coding, refactors, Cursor agent | `code` | 8k output cap; Mistral/OpenAI mid-tier; 32–128k context |
| Hermes routine on tower | `hermes-fast` | Same cost profile as `cheap`; tuned for smalshi loops |
| Hermes high-stakes reasoning | `hermes-smart` | 16k output cap; Claude Sonnet 200k context when Anthropic key set |
| Quality review pass | `review` | High tier; use sparingly (`make cost-review`) |
| No cloud / LAN only | `offline` | Ollama first; minimal cloud fallback |

## Rules of thumb

1. **Input size** — If your prompt + files exceed ~80% of the model `context_window` in the catalog, switch to a larger-window preset (`hermes-smart`, `code`) or trim context.
2. **Output size** — `max_tokens_default` on each preset is the LiteLLM cap (`make sync-preset-tokens` keeps YAML in sync). Do not raise caps without checking `make usage-rollup`.
3. **Cost** — Larger context + higher tiers cost more. Prefer `cheap` / `hermes-fast` until `route_policy` or quota pressure suggests otherwise.
4. **Embeddings** — `openai/text-embedding-3-small` is catalog-only (8k); not a chat preset.

## Ops

```bash
make check-catalog      # presets, models, max_tokens, context_window
make usage-rollup       # 24h traffic by model (JSON logs)
make homelab-status     # includes usage rollup header
```

See `docs/CONSOLE_SPEC.md` for the widget grid. Connectors: `docs/CONNECTOR_SPEC.md`, `make connect-provider`.

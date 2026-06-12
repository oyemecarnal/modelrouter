# Policy router (plain language)

## What is it?

Think of ModelRouter as a **smart receptionist** for AI models, not a single phone number.

Instead of every app choosing “GPT-4” or “Groq” by name, they ask for a **job type**:

| You ask for | Meaning |
|-------------|---------|
| `hermes-fast` | Quick, cheap work — status, short answers, simple steps |
| `hermes-smart` | Serious thinking — plans, money, config, multi-step reasoning |
| `cheap` | Lowest cost anywhere in the system |
| `code` | Writing or fixing code |
| `review` | Careful quality pass |
| `offline` | Stay on your Mac (Ollama); cloud only if local fails |

ModelRouter picks the **cheapest model that’s good enough**, and **steps up or down** if a provider is down or out of quota.

## Hermes on smalshi (mini → tower)

- **Composed** on the Mac mini, **runs** on kc-tower.
- Point Hermes at ModelRouter on the mini (or tower if you tunnel): base URL `http://<mini>:3000`.
- **Routine loops** → model `hermes-fast` (Groq 8B / Mistral small).
- **Big decisions** → model `hermes-smart` (GPT-4o / Groq 70B with fallbacks).

You don’t change provider keys in the agent — only the **preset name**.

## Closing the loop (widget → routing)

The **Keys widget** shows who’s running out of quota (Codex, Groq, etc.).

`route_policy.py` reads that snapshot and writes `data/route_hints.json`, e.g.:

> “OpenAI pressure 72% — use `cheap` instead of `hermes-smart`.”

Agents or MCP can call `route_recommend` before each run. Over time this becomes automatic downshifting when you’re near limits.

## Per-project virtual keys

Each project (Hermes, Kalshi bot, coinbot, Cursor) gets its **own API key** to ModelRouter:

- Today (native / venv): keys may map to the same gateway, but you **label** who called.
- Tomorrow (Docker + Postgres): LiteLLM tracks **spend per project** and rate limits.

Run `make project-keys` to add `MODELROUTER_KEY_*` vars to `.env`.

## Running all projects through ModelRouter

**Yes, when it makes sense:**

- **Good fit:** anything that already uses an OpenAI-style API (agents, bots, Cursor).
- **Keep direct:** ultra-low-latency paths, or tools that need one vendor’s special feature.

**Tower vs mini:** Polygon and some secrets may live on the **mini** while bots run on **tower**. ModelRouter on the mini is the **single front door**; tower clients use `http://Kevins-Mac-mini.local:3000` (or Tailscale). Keys stay on the mini — tower doesn’t duplicate `.env` files.

## OpenRouter — do you need it?

**No, not for your setup today.** You already have OpenAI, Gemini, Groq, Mistral, and local Ollama.

OpenRouter (~$5+/mo minimum useful spend) is a **convenience backup**: one API for rare models you haven’t wired. We left it **stubbed** in `config/openrouter.stub.yaml`. Enable only if you hit a model you can’t get elsewhere.

## Offline / air-gapped (item 9)

`offline` preset = **local Ollama first**. If Ollama isn’t running, **one** cloud backup (`groq-fast`) kicks in — not the full fallback chain. That’s “stay local unless broken,” not “never use cloud.”

## Cost review (occasionally)

Before adding providers, presets, or agent loops, ask:

> **Is there already a better tool — cheaper or saves model use?**

```bash
make cost-review
```

See `docs/COST_REVIEW.md` and `config/cost_alternatives.yaml`. OpenRouter stays stubbed unless you truly need exotic models.

## MCP control plane

The ModelRouter MCP server lets Cursor/agents **ask**:

- Are you up? (`health`)
- What presets exist? (`list_models`)
- What should Hermes use right now? (`route_recommend`)

See `make mcp-install` and `.cursor/mcp.json.example`.

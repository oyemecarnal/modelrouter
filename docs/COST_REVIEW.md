# Cost review — “Is there already a better tool?”

Run this **occasionally** (monthly, or before adding a provider / preset / agent loop):

```bash
make cost-review
```

## The question

> **Is there already a better tool for this job — one that’s cheaper, good enough, or avoids model calls entirely?**

If **yes**, prefer that tool. ModelRouter stays the front door for what still needs an LLM.

## Decision flow (plain language)

1. **What is the job?** (code, chat, status, search, embed, trade signal, etc.)
2. **Does it need an LLM at all?** Scripts, SQL, grep, rules, cron, and APIs often don’t.
3. **If yes — what’s the cheapest tier that won’t break context?**
   - Routine → `cheap` / `hermes-fast`
   - Code → `code`
   - Money / config / strategy → `hermes-smart` / `review`
   - No cloud → `offline`
4. **Is a non-LLM product already paid for and better?**
   - Cursor Tab / inline vs full `smart` chat
   - Codex / Copilot subscription vs raw OpenAI API
   - Local Ollama vs cloud for bulk/offline
5. **If we still need ModelRouter — is routing right?** Check widget + `make route-hints`.

## Often “yes, use something else”

| Job | Often better / cheaper | Instead of |
|-----|------------------------|------------|
| Find a symbol in repo | `rg`, IDE search | `smart` chat |
| Format JSON / YAML | `jq`, formatter | any model |
| Lint / typecheck | `ruff`, `tsc`, CI | `code` preset |
| Scheduled health | `make doctor`, cron | agent poll loop |
| Key / quota visibility | Keys widget | custom scraper + LLM |
| Embeddings at scale | local Ollama embed model | OpenAI embedding API |
| Rare exotic model | OpenRouter (stubbed) | wiring 5 providers — only if truly needed |
| Coding in Cursor | Tab + fast model | `smart` for every message |

## Often “no, ModelRouter is right”

- **Hermes / agents** on tower → one gateway on mini (`hermes-fast` / `hermes-smart`)
- **Multi-provider fallbacks** when quotas bite
- **Per-project keys** and one place to rotate secrets
- **Policy presets** so apps don’t hardcode vendor names

## When to reconsider ModelRouter itself

Ask separately: *Should this app talk to a vendor directly?*

- **Keep ModelRouter** when: fallbacks, presets, central keys, or multi-project routing matter.
- **Skip ModelRouter** when: one static model, one key, no fallback, ultra-simple script — maybe direct Groq/OpenAI is fine.

## Record outcomes

After each review, note in `data/cost_review_log.md` (optional):

- Date
- What you considered
- Decision: keep / switch tool / change preset
- Estimated savings (rough)

## Tie-in to the stack

- `make doctor` — up? keys? presets?
- `make route-hints` — widget says downshift?
- `config/projects.yaml` — each project on the right preset?
- `config/cost_alternatives.yaml` — living list of “use X instead of Y”

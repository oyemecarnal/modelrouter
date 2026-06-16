# Tower agent cleanup (CLEAN_WIRES)

Provider API keys belong on **kc-mini** only. Tower agents use `~/.config/modelrouter/client.env` for gateway auth — not vendor secrets.

## Audit

```bash
make audit-tower-wires
```

Exits 0 when clean. Skips `OPENAI_API_KEY` in `client.env` when it is the **gateway virtual key** (OpenAI-compatible shim).

## Fix workflow

```bash
make clean-tower-wires    # rewrite client.env + re-audit
make smoke-tower
```

## Common stray: coinbot `.env`

If audit reports:

```
stray OPENAI_API_KEY in /root/dev/coinbot/.env
```

**On kc-tower:**

1. Remove `OPENAI_API_KEY` (and any `GROQ_API_KEY`, `ANTHROPIC_API_KEY`, etc.) from `~/dev/coinbot/.env`
2. Ensure the bot sources gateway client env:

```bash
source ~/.config/modelrouter/client.env
# OPENAI_API_BASE / OPENAI_API_KEY point at mini gateway
```

3. Re-run from laptop: `make audit-tower-wires`

## Rules

| Location | Allowed |
|----------|---------|
| `~/.config/modelrouter/client.env` | `OPENAI_API_BASE`, gateway `OPENAI_API_KEY` (master/virtual) |
| `~/dev/*/.env` on tower | **No** provider `*_API_KEY` |
| kc-mini `~/dev/modelrouter/.env` | All provider keys |

See `docs/CLEAN_WIRES.md`, `docs/TOWER_WIRING.md`.

# Cursor → ModelRouter wiring

Cursor must call **your gateway**, not OpenAI directly. This is the main Phase 0 human step.

## Settings (Cursor → Models → OpenAI)

| Field | Value |
|-------|--------|
| **OpenAI API Base URL** | `http://127.0.0.1:3000/v1` (laptop dev) |
| **API Key** | `MODELROUTER_MASTER_KEY` from `modelrouter/.env` |
| **Override OpenAI Base URL** | **On** |

Keep `crsr_*` as the master key unless you intentionally rewire Cursor after `make rotate-master-key`.

## Do not confuse

| Variable | Purpose |
|----------|---------|
| `MODELROUTER_MASTER_KEY` | Gateway bearer — **use this in Cursor** |
| `CURSOR_API_KEY` | Cursor product / widget usage API — **not** the gateway key |
| `OPENAI_API_KEY` | Provider key on **kc-mini only** — not in Cursor |

## Verify (automated)

```bash
make daemon-enable    # optional: auto-start at login (see docs/LAPTOP_DAEMON.md)
make restart          # if gateway down
make smoke-cursor     # models + chat + log check
```

## Verify (manual)

1. Send one chat in Cursor.
2. `tail -5 data/modelrouter.log` — look for JSON `request_success` with `"model":"fast"` or your preset.
3. `make cost-review` — confirm traffic should flow through presets.

## Models in Cursor

Use gateway aliases: `smart`, `fast`, or policy presets (`cheap`, `code`, `hermes-fast`) if your Cursor build allows custom model names.

## LAN note

Production agents on **kc-tower** use `http://Kevins-Mac-mini.local:3000/v1` — see `config/client.env.example`. Laptop Cursor typically uses `127.0.0.1`.

# ModelRouter homelab goals

**Role:** Self-hosted LLM gateway — OpenAI-compatible front door for a multi-machine homelab (`docs/PRODUCT_VISION.md`).

## North star (homelab)

One **on-LAN front door** for LLM calls on an always-on gateway host, with a laptop for dev and a remote host for agent/bot **runtime**. SSH aliases live in `config/hosts.yaml` / `config/hosts.local.yaml`.

**Before calibration:** untangle all wires (`docs/CLEAN_WIRES.md`) — new ModelRouter API key, no provider keys on clients, one meter.

## Principles

1. **Policy, not vendors** — clients use presets (`hermes-fast`, `cheap`, `code`), not `gpt-4o`.
2. **Keys on mini** — tower/laptop call the gateway; don't duplicate `.env` on every host.
3. **Fail down, not up** — fallbacks go cheaper/local before expensive.
4. **Cost discipline** — `make cost-review`; OpenRouter stubbed unless exotic models needed.
5. **Simple ops** — `make doctor`, `make homelab-status`, `make deploy-mini`.

## Machines

| Host | Role |
|------|------|
| **kc-mini** | Gateway, keys, compose smalshi, deploy target |
| **kc-tower** | Hermes, Kalshi, coinbot runtime → calls mini via Tailscale (`docs/TOWER_WIRING.md`) |
| **laptop** | Dev, Cursor, widget, push to mini |

## Iteration cycle

Versions `1.1` → `1.5` per cycle. See `docs/iterations/`. Agent playbook: `docs/CYCLES.md` (repo-local `/cycle` slash commands in `.cursor/commands/`).

## Human backlog

- [x] Master key — keep `crsr_*` as `MODELROUTER_MASTER_KEY` (Cursor-compatible gateway bearer)
- [x] `LITELLM_SALT_KEY` — distinct salt set (`make rotate-salt-key` if rotating; master unchanged)
- [x] Cursor → ModelRouter — verified in Cursor settings (`docs/CURSOR_WIRING.md`)
- [x] `ANTHROPIC_API_KEY` on kc-mini — `review` / `hermes-smart` Anthropic routes
- [x] Groq key — rotation waived (key OK)
- [x] `gateway-tower` SSH aliases in `~/.ssh/config` + `config/hosts.yaml`
- [x] **Tailscale** between operator laptop and runtime host
- [x] `make push-client-env-tower` — client.env uses gateway Tailscale URL
- [x] Tower agent `.env` cleanup — coinbot `OPENAI_API_KEY` removed; gateway via `client.env` (`docs/WHY_MODELROUTER.md`)

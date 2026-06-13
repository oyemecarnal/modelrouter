# ModelRouter homelab goals

**Role:** Core AI gateway for Kevin's homelab — seed of a **purchase/SaaS product** (`docs/PRODUCT_VISION.md`).

## North star (homelab)

One **on-LAN front door** for LLM calls: `http://Kevins-Mac-mini.local:3000` on kc-mini (always-on), with laptop for dev and tower for agent/bot **runtime**. Use `kc-mini-lan` for SSH only.

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
| **kc-tower** | Hermes, Kalshi, coinbot runtime → calls mini |
| **laptop** | Dev, Cursor, widget, push to mini |

## Iteration cycle

Versions `1.1` → `1.5` per cycle. See `docs/iterations/`. Agent playbook: `docs/CYCLES.md` (repo-local `/cycle` slash commands in `.cursor/commands/`).

## Human backlog

- [x] Master key — keep `crsr_*` as `MODELROUTER_MASTER_KEY` (Cursor-compatible gateway bearer)
- [x] `LITELLM_SALT_KEY` — rotate with `make rotate-salt-key` (does not change master)
- [ ] Confirm Cursor base URL → ModelRouter (not direct OpenAI) — see `docs/CURSOR_WIRING.md`, `make smoke-cursor`
- [ ] `ANTHROPIC_API_KEY` on kc-mini when available — `make push-env-mini`; see `docs/KEY_ROTATION.md`
- [ ] Rotate Groq key (prior chat exposure) — see `docs/KEY_ROTATION.md`
- [x] `kc-tower` SSH aliases in `~/.ssh/config` + `config/hosts.yaml`
- [ ] `make push-client-env-tower` when tower is online (`make smoke-tower` to verify)
- [ ] `LITELLM_SALT_KEY` — set distinct salt before Docker/Postgres (`make rotate-master-key` rotates master too)

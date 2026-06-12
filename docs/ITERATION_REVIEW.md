# Iteration cycle 1 review (v1.1 → v1.5)

**Date:** 2026-06-12  
**Reviewer:** AI code review (Bugbot) + homelab goals pass  
**Tests run:** `make test` ✓ · `make lint` ✓ · `make health` ✓ (after restart) · mini health ✓ · `remote-health` partial (tower SSH TBD)

---

## What this cycle delivered

| Ver | Focus | Status |
|-----|--------|--------|
| 1.1 | `VERSION`, `HOMELAB_GOALS`, `make test` | Done |
| 1.2 | `config/hosts.yaml`, `make remote-health` | Done |
| 1.3 | `docs/GITHUB.md`, CI smoke expanded | Done |
| 1.4 | `make lint` | Done |
| 1.5 | `make homelab-status`, `CHANGELOG` 1.5.0 | Done |

Plus prior work in same tree: policy presets, doctor, cost-review, MCP, route_policy, keys widget.

---

## Changes we **should** make (next cycle 2.x)

### Must fix (reliability & security)

1. **Rotate master key** — still placeholder; `make rotate-master-key` then update Cursor + tower clients. *(Human)*
2. **Daemon stability** — process still dies intermittently; plist `KeepAlive` + slow start caused thrash (mitigated: health fail now exit 0). Next: run `litellm` under `start.sh` only, pidfile track litellm child, or use launchd `ThrottleInterval`.
3. **MCP reads `.env`** — fixed this cycle; copy real key into `.cursor/mcp.json` (not committed).
4. **`route_hints.json` multi-project** — fixed: `--all` now writes full dict.
5. **`ANTHROPIC_API_KEY`** — empty; `hermes-smart`/`review` lean on OpenAI/Groq until filled. *(Human)*

### Should change (homelab simplicity)

6. **`KC_TOWER_SSH`** — confirm tower hostname in `~/.ssh/config`; add to `docs/HOMELAB_GOALS.md` when known. *(Human)*
7. **Single env template for tower** — `config/client.env.example` with only `OPENAI_BASE_URL=http://kc-mini-lan:3000/v1` + project key — no provider keys on tower.
8. **`make deploy-mini` post-hook** — auto `make remote-health` on success.
9. **install shellcheck** on laptop/mini — `brew install shellcheck` for real lint.
10. **Widget auto-restart** — optional launchd for keys panel (like gateway).

### Could do (why / why not)

| Idea | Why | Why not |
|------|-----|---------|
| **OpenRouter $5/mo** | Exotic models, one bill | You already cover 95% with Groq/Mistral/OpenAI/Gemini; stub is enough (`make cost-review`) |
| **Docker+Postgres on mini** | Real virtual keys + spend caps | Ops weight; native venv works; defer until multi-user or billing pain |
| **Prometheus metrics** | Dashboards, SLOs | Homelab overkill until gateway flaps are fixed |
| **Best-of-N routing** | Quality arbitration | Token cost 2–3×; use for strategy_lab experiments only |
| **Menu bar widget (7)** | Always-visible quota | pywebview v1 is enough; WidgetKit is a 2.x project |
| **1Password Connect** | Headless secrets | CLI-free containers; wait until Docker is default deploy |
| **GitHub Actions deploy to mini** | Push → auto deploy | Security + SSH from cloud; manual `make deploy-mini` is fine for homelab |

### Should **undo** or simplify

| Item | Reason |
|------|--------|
| **Duplicate preset YAML** in `minimal` + `full` | Drift risk — cycle 2: generate from `config/includes/policy_presets.yaml` |
| **`OPENROUTER_API_KEY` in .env`** if unused | Confusing in doctor; remove or comment until stub enabled |
| **`.env` on laptop with keys + mini copy** | Prefer mini as canonical; laptop sync via `keys-sync-mini` only |
| **Hardcoded `/Users/kevinreed` in plist/mcp example** | Cycle 2: `MODELROUTER_ROOT` or install script templating |
| **rsync accidentally synced `.git` once** | Fixed exclude; verify mini isn't a git clone unless intended |

### Keep (core homelab value)

- Policy presets (`hermes-fast` / `hermes-smart`)
- `config/hosts.yaml` + `config/projects.yaml`
- `make doctor`, `homelab-status`, `cost-review`
- Keys widget + `route_policy` loop
- OpenRouter **stub** (not wired)
- `deploy-mini` + `push-env-mini` split (code vs secrets)

---

## Cost-effective tool check (standing question)

Run `make cost-review` each cycle. This cycle's answer: **ModelRouter stays the gateway**; don't add OpenRouter; prefer presets over `smart`; use widget + route hints instead of new dashboards.

---

## Next cycle 2.1 proposal

1. `make rotate-master-key` + tower client env template  
2. Daemon hardening (plist runs `start.sh` directly)  
3. YAML preset merge script (one source of truth)  
4. Confirm `kc-tower-lan` SSH  

---

## Test log (cycle 1 end)

```
make test     → PASS (gateway optional skip if down)
make lint     → PASS
make health   → alive (laptop + mini after restart)
remote-health → laptop+mini alive; tower skip
Bugbot        → 7 findings; 4 patched in-cycle
```

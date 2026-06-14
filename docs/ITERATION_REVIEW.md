# Iteration cycle 3 review (v3.1 → v3.5)

**Date:** 2026-06-12  
**Ship:** **v3.0.0** (`main`)  
**Tests:** `make test` ✓ · `make lint` ✓ · `make doctor` ✓ (when running) · `deploy-mini` ✓ · `remote-health` laptop+mini ✓

---

## What cycle 3 delivered

| Ver | Focus | Status |
|-----|--------|--------|
| 3.1 | Daemon pid, 0.0.0.0 health bind, salt warn, LAN URL docs | Done → v2.5.1 |
| 3.2 | `stop.sh` port cleanup; doctor safe when gateway down | Done |
| 3.3 | `deploy-mini` — kc-mini on 3.x tree | Done |
| 3.4 | Committee checkpoint, CLEAN_WIRES/HOMELAB human split | Done |
| 3.5 | Cycle capstone docs → **v3.0.0** | Done |

**Phase 0:** ~85% — gateway ops trustworthy; calibration prep unlocked. Console still deferred.

---

## Human actions (before Phase 1)

| Action | Why |
|--------|-----|
| Verify Cursor → ModelRouter URL + master key | Clean wires metering |
| `make push-client-env-tower` when tower online | Hermes/bots on gateway |
| Add `ANTHROPIC_API_KEY` on mini | `hermes-smart` / `review` |
| Rotate Groq key | Prior exposure |
| Decide: keep `crsr_*` master vs `sk-mr-*` rotate | Namespace purity vs Cursor friction |

---

## Next cycle 4 proposal (Phase 1 start)

1. `config/models_catalog.yaml` — context, cost tier, free/paid  
2. Console MVP spec (`docs/CONSOLE_SPEC.md`) — static grid only  
3. Per-preset max tokens in YAML  
4. Tower online + client.env deploy  

---

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
2. **Daemon stability** — pidfile reconciled from port listener in `start-daemon.sh` (`modelrouter_reconcile_pidfile`). launchd: `make daemon-enable`.
3. **MCP reads `.env`** — fixed this cycle; copy real key into `.cursor/mcp.json` (not committed).
4. **`route_hints.json` multi-project** — fixed: `--all` now writes full dict.
5. **`ANTHROPIC_API_KEY`** — on kc-mini *(done)*

### Should change (homelab simplicity)

6. **`KC_TOWER_SSH`** — confirm tower hostname in `~/.ssh/config`; add to `docs/HOMELAB_GOALS.md` when known. *(Human)*
7. **Single env template for tower** — `config/client.env.example`; tower uses Tailscale URL `http://100.85.245.23:3000/v1` (`docs/TOWER_WIRING.md`)
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

---

## Cycle 7 checkpoint (v3.7.0)

**Theme:** Phase 0 + Phase 1 complete; calibration ops wired.

| Iter | Deliverable |
|------|-------------|
| 7.1 | Snapshot export must not contain raw API key prefixes (`test.sh`) |
| 7.2 | Pidfile reconcile before optional health in `make test` |
| 7.3 | `context_window` enforced in `check_catalog`; `docs/CONTEXT_GUIDE.md` |
| 7.4 | `usage-rollup` in `homelab-status`; doctor next steps |
| 7.5 | `PRODUCT_VISION` phase markers; **v3.7.0** |

**Human backlog (unchanged):** Remove stray provider keys on tower agent `.env` if any remain (`CLEAN_WIRES.md`).

**Next cycle 8 proposal:** Phase 2 connector MVP sketch — `docs/CONNECTOR_SPEC.md` draft, one provider paste-key flow.

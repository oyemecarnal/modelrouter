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

---

## Cycle 8 checkpoint (v3.8.0)

**Theme:** Phase 2 start — Groq paste-key connector.

| Iter | Deliverable |
|------|-------------|
| 8.1 | `CONNECTOR_SPEC.md` — security model, vault rules |
| 8.2 | `env_store.py` — atomic `.env` updates |
| 8.3 | Groq `gsk_` validation + `test.sh` smoke |
| 8.4 | `make connect-groq` — paste → mini deploy |
| 8.5 | Phase 2 markers; **v3.8.0** |

**Next cycle 9 proposal:** `connect-anthropic`, widget connector status row (no key display), `config/connectors.yaml` registry.

---

## Cycle 9 checkpoint (v3.9.0)

**Theme:** Anthropic connector + stereo receiver connectivity bar.

| Iter | Deliverable |
|------|-------------|
| 9.1 | Connector scripts + Anthropic validation in `test.sh` |
| 9.2 | `make connect-anthropic`, `docs/ENV.md` |
| 9.3 | Widget receiver — 5 theme presets, Classic R/G default |
| 9.4 | `homelab_status` — paths, API keys, network LED rows |
| 9.5 | **v3.9.0** (shipped in v3.10.0 bundle) |

**Next cycle 10 proposal:** `config/connectors.yaml` registry, generic `connect-provider.sh`, optional `smoke-hermes-smart`.

---

## Cycle 10 checkpoint (v3.10.0)

**Theme:** Connector registry SSOT + Anthropic route smoke.

| Iter | Deliverable |
|------|-------------|
| 10.1 | `connectors.yaml` validation — no secrets, required fields |
| 10.2 | `make smoke-hermes-smart` — hermes-smart via mini gateway |
| 10.3 | Registry ↔ `connect-{id}.sh` mapping in `test.sh` |
| 10.4 | `connect-provider` + smoke in README / ENV / doctor |
| 10.5 | **v3.10.0** (shipped) |

**Next cycle 11 proposal:** Tower `.env` cleanup (`CLEAN_WIRES`), landing blurb from `POSITIONING.md`, third connector (OpenAI paste-key).

---

## Cycle 11 checkpoint (v3.11.0)

**Theme:** Clean tower wires + OpenAI paste-key connector.

| Iter | Deliverable |
|------|-------------|
| 11.1 | `make audit-tower-wires` — stray provider keys on kc-tower |
| 11.2 | `check-key-hygiene` tower audit hint; soft skip when offline |
| 11.3 | `make connect-openai` + registry (3 connectors) |
| 11.4 | README positioning blurb + ops docs |
| 11.5 | **v3.11.0** |

**Next cycle 12 proposal:** Landing/purchase stub (`docs/LANDING.md`), Mistral connector, widget connector row from registry.

---

## Cycle 12 checkpoint (v3.12.0)

**Theme:** Landing stub, Mistral connector, registry-driven receiver.

| Iter | Deliverable |
|------|-------------|
| 12.1 | Audit whitelist for tower `client.env` gateway shim |
| 12.2 | `make clean-tower-wires` |
| 12.3 | `make connect-mistral` (4 registry connectors) |
| 12.4 | `homelab_status` ← `connectors.yaml`; `docs/LANDING.md` |
| 12.5 | **v3.12.0** |

**Next cycle 13 proposal:** Google/Gemini connector, widget signup links from registry, tower coinbot `.env` cleanup.

---

## Cycle 13 checkpoint (v3.13.0)

**Theme:** Google connector + registry signup links + tower cleanup docs.

| Iter | Deliverable |
|------|-------------|
| 13.1 | `GOOGLE_API_KEY` validation (`AIza…`) |
| 13.2 | `docs/TOWER_CLEANUP.md`, coinbot audit hints |
| 13.3 | `make connect-google` (5 registry connectors) |
| 13.4 | Widget signup strip from `connectors.yaml` |
| 13.5 | **v3.13.0** |

**Next cycle 14 proposal:** DeepSeek/Together connectors, widget “Add provider” button, `make daemon-enable` laptop doc pass.

---

## Cycle 14 checkpoint (v3.14.0)

**Theme:** More connectors, widget Add Provider, laptop daemon SSOT.

| Iter | Deliverable |
|------|-------------|
| 14.1 | DeepSeek + Together validation |
| 14.2 | `docs/LAPTOP_DAEMON.md` |
| 14.3 | 7 registry connectors |
| 14.4 | Widget **＋ Provider** menu |
| 14.5 | **v3.14.0** |

**Next cycle 15 proposal:** Fireworks/Cohere connectors, tower coinbot cleanup automation, Personal tier tarball script.

---

## Cycles 15–18 batch (v3.15.0 → v3.18.0)

| Cycle | Theme | Version |
|-------|--------|---------|
| 15 | Fireworks + `make package-personal` | v3.15.0 |
| 16 | Cohere connector (9 registry) | v3.16.0 |
| 17 | `make guide-tower-strays` | v3.17.0 |
| 18 | Capstone docs + ship bundle | v3.18.0 |

**Next cycle 19 proposal:** OAuth spec stub, widget paste modal, `make daemon-enable` runbook on laptop.

---

## Cycle 19 checkpoint (v3.19.0)

**Theme:** Explain value + optional tower exceptions (coinbot clarity).

| Iter | Deliverable |
|------|-------------|
| 19.1 | `docs/WHY_MODELROUTER.md` |
| 19.2 | `config/wire_exceptions.yaml` + audit filter |
| 19.3 | `test.sh` wire_exceptions smoke |
| 19.4 | README / HOMELAB_GOALS links |
| 19.5 | `OAUTH_CONNECTOR_STUB.md` · **v3.19.0** |

**Next cycle 20 proposal:** Widget paste modal, `make daemon-enable` one-liner in doctor when gateway down, coinbot gateway wiring script.

---

## Cycle 20 checkpoint (v3.20.0)

**Theme:** Widget paste-key UX + tower hygiene automation.

| Iter | Deliverable |
|------|-------------|
| 20.1 | Audit `.env.*` · `make strip-tower-llm-keys` |
| 20.2 | Doctor gateway-down fix block |
| 20.3 | Widget paste modal · `/connectors/paste` |
| 20.4 | `connector_paste.py` + tests |
| 20.5 | Tower `.env.cursor` cleaned · **v3.20.0** |

**Next cycle 21 proposal:** OAuth spec draft, widget push/restart toggle, laptop `make daemon-enable` one-shot in homelab-status when gateway down.

---

## Cycle 21 checkpoint (v3.21.0)

**Theme:** OAuth roadmap + gateway-down visibility.

| Iter | Deliverable |
|------|-------------|
| 21.1 | `docs/OAUTH_CONNECTOR_SPEC.md` |
| 21.2 | `homelab_status.hints` · homelab-status fix lines |
| 21.3 | Widget push/restart toggles |
| 21.4 | Receiver bar hints + tests |
| 21.5 | **v3.21.0** |

**Next cycle 22 proposal:** Ship v3.21.0, `make daemon-enable` run on laptop, OAuth pilot spike (google callback stub only).

---

## Cycle 22 checkpoint (v3.22.0)

**Theme:** Ship readiness + laptop gateway auto-fix + OAuth dev stub.

| Iter | Deliverable |
|------|-------------|
| 22.1 | `make ensure-gateway` |
| 22.2 | `make oauth-start` · callback stub |
| 22.3 | `make ship-check` |
| 22.4 | `docs/SHIP_CHECKLIST.md` |
| 22.5 | **v3.22.0** ship-ready |

**Next cycle 23 proposal:** Run `/ship v3.22.0`, `make deploy-mini`, implement first OAuth exchange (google) behind feature flag.

---

## Ship status (2026-06-12)

**Origin:** **v3.27.0**. **Tower:** audit ✓. **Mini:** gateway ok. **Laptop gateway:** run `make doctor-fix` if down

---

## Cycle 24 checkpoint (v3.24.0)

**Theme:** Widget refresh reliability + vault operational visibility.

| Iter | Deliverable |
|------|-------------|
| 24.1 | Vault masked export tests |
| 24.2 | Equity fetch timeout (90s) + stale cache |
| 24.3 | Stale flag on timeout path |
| 24.4 | Doctor + homelab vault hints |
| 24.5 | **v3.24.0** |

**Next cycle 25 proposal:** Gateway 429 key cycling, OAuth google stub, widget vault disable UI.

---

## Cycle 25 checkpoint (v3.25.0)

**Theme:** Vault export safety + route-policy key cycling hints.

| Iter | Deliverable |
|------|-------------|
| 25.1 | Vault export deny (`MODELROUTER_KEY_*`, exchange secrets) |
| 25.2 | Route `key_hints` when quota hot + vault alternates |
| 25.3 | Tangem `.env.local.example` placeholders |
| 25.4 | `make doctor-fix` |
| 25.5 | **v3.25.0** |

**Next cycle 26 proposal:** Wire gateway 429 → vault `select_key`, widget vault disable UI, OAuth google exchange stub.

---

## Cycle 26 checkpoint (v3.26.0)

**Theme:** 429 rotate hints, widget vault toggles, OAuth exchange pilot.

| Iter | Deliverable |
|------|-------------|
| 26.1 | OAuth state validation + Google exchange behind `OAUTH_EXCHANGE=1` |
| 26.2 | Gateway 429 → `record_rate_limit` + rotate hints file |
| 26.3 | Widget key vault panel + `/vault/toggle` |
| 26.4 | OAuth callback state generation + doctor rotate hints |
| 26.5 | **v3.26.0** |

**Next cycle 27 proposal:** Hot-swap `.env` on 429 (or LiteLLM alt-key routes), gateway auto-export hook, Tangem live verify.

---

## Cycle 27 checkpoint (v3.27.0)

**Theme:** Tangem ETH fallback, 429 export hook, launchd bootstrap.

| Iter | Deliverable |
|------|-------------|
| 27.1 | `daemon-enable` bootstrap/bootout (modern macOS) |
| 27.2 | Widget fetch → modelrouter `.venv` (SSL fix) |
| 27.3 | ETH RPC fallback for watch wallets |
| 27.4 | `make vault-rotate-export` after 429 hints |
| 27.5 | **v3.27.0** |

**Next cycle 28 proposal:** LiteLLM `__ALT_N` model routes, auto `vault-rotate-export` on 429, push-env-mini after rotate.

# AI Committee Review — v1.5.0 (full project)

**Date:** 2026-06-12  
**Commit:** `7576096` on `main`  
**Panels:** Bugbot (code) · Security Review · Architecture/Product  
**Ops baseline:** `make test` ✓ · `make lint` ✓ · gateway **down** on laptop & mini at review time

---

## Verdict

| Dimension | Grade | Summary |
|-----------|-------|---------|
| Architecture | **B+** | Layered harness matches `PRODUCT_VISION.md`; preset YAML drift and dual deploy paths weaken coherence |
| Homelab wiring | **C+** | Topology designed; Phase 0 clean wires ~40% done |
| Security | **Yellow** | Read-only inventory/wallets good; LAN gateway + unauthenticated widget writes are main risks |
| Code quality | **B** | 8 actionable bugs; none blocking homelab if gateway restarted |
| Product readiness | **Phase 0** | Do not start Console until clean wires + daemon trust |

**Primary recommendation:** Cycle 2 = **finish Phase 0**, not feature expansion.

---

## Must fix (P0)

### Security
1. **LAN gateway = single bearer** — placeholder defaults still allowed at startup; `MODELROUTER_KEY_*` copies master in native mode. → `make rotate-master-key`, fail-closed on placeholders, tower firewall/Tailscale.
2. **Widget HTTP writes unauthenticated** — `/keys/add`, `/wallets/add`, `/api-assess` on `127.0.0.1:8765` with no session token. → Add local auth token or restrict to editor-only key path.

### Reliability / bugs
3. **Gateway down** — doctor: daemon not running on laptop & mini; presets missing from `/v1/models`. → `make restart` on mini; `make deploy-mini`.
4. **Project keys stale after rotate** — `rotate-master-key` does not refresh `MODELROUTER_KEY_*`. → Re-run `issue-project-keys` after rotation or document mandatory step.
5. **Equity status.json short-circuit** — `fetch_equity` returns cached coinbot status before live fetch; can show paper equity. → Prefer live when `force_live`; or skip status when brokers configured.
6. **`route_hints.json` schema clash** — single-project `recommend()` overwrites multi-project `--all` output.

### Homelab (human)
7. **Tower SSH** — `kc-tower-lan` unreachable; roll out `config/client.env.example`.
8. **`ANTHROPIC_API_KEY` empty** — `hermes-smart` / `review` lean on OpenAI/Groq.

---

## Should fix (P1)

| # | Issue | Location |
|---|--------|----------|
| 1 | Equity total skips assets after 6 priced alts | `equity_remote_runner.py` |
| 2 | API assess presets empty (`preset_models` is list not dict) | `api_assess.py` |
| 3 | MCP `list_models` crashes when gateway down | `mcp_server.py` |
| 4 | `client.env.example` shell expansion won't work in dotenv | `client.env.example` |
| 5 | Snapshot exposes full wallet addresses locally | `fetch_wallets.py` / widget |
| 6 | Preset YAML triplicated (drift) | `modelrouter.yaml`, `.minimal.yaml`, `includes/` |
| 7 | `push-env-mini` / `sync-keys` blast radius growing | Makefile, sync-keys.sh |

---

## Could defer

- Console Web UI, Docker+Postgres on mini, OpenRouter wiring, OAuth connectors
- Prometheus, GitHub Actions deploy-to-mini, WidgetKit menu bar
- Best-of-N routing, billing tiers, `models_catalog.yaml` (until Phase 0 green)

---

## Cycle 2 plan (committee-approved)

| Ver | Focus | Exit criteria |
|-----|--------|---------------|
| **2.1** | Clean wires: rotate key, tower `client.env`, SSH | doctor green; tower→mini health |
| **2.2** | Daemon reliability + deploy post-health | 48h uptime; `deploy-mini` verifies remote |
| **2.3** | Preset SSOT from `policy_presets.yaml` | CI catches drift |
| **2.4** | Inventory-driven key consolidation | keys on kc-mini only |
| **2.5** | Polish: widget launchd, shellcheck, Anthropic key | `homelab-status` all green |

---

## What to keep

- Policy presets + `route_policy` widget loop
- OpenRouter **stub**
- Keys widget as quota/catalog seed (not Console yet)
- `make doctor`, `homelab-status`, `cost-review`, inventory harness
- `deploy-mini` + `push-env-mini` split

---

## Standing cost question

**Keep ModelRouter as gateway.** Do not enable OpenRouter by default. Use presets + widget + route hints instead of new dashboards or aggregators.

---

## Panel references

- Code: Bugbot review (`7576096` vs `126381d`)
- Security: full-project security review
- Architecture: `PRODUCT_VISION.md`, `HOMELAB_GOALS.md`, `CLEAN_WIRES.md`, `ITERATION_REVIEW.md`

Next committee checkpoint: end of cycle 2.5 → update this doc + `ITERATION_REVIEW.md`.

---

## Cycle 2–3 checkpoint (2026-06-12)

**Commits:** `9dec9b1` (v2.5.0) · `2a44976` (homelab ops) · `ce513e1` (v2.5.1) · cycle 3 → **v3.0.0**

| P0 item | Status |
|---------|--------|
| Fail-closed master key | **Fixed** — `check-master-key.sh` |
| Widget POST auth | **Fixed** — `X-Widget-Token` |
| Project keys after rotate | **Fixed** — `--refresh` |
| route_hints schema clash | **Fixed** |
| Equity / api_assess / MCP bugs | **Fixed** |
| Gateway down / daemon pid | **Improved** — `start.sh`, `stop.sh`, health bind |
| Tower client.env | **Script ready** — tower SSH offline (human) |

| Dimension | Was | Now |
|-----------|-----|-----|
| Homelab wiring | C+ | **B** — mini deployed, LAN URL documented |
| Security | Yellow | **Yellow→Green-ish** — widget auth + fail-closed; LAN bearer unchanged |
| Product readiness | Phase 0 ~40% | **Phase 0 ~85%** — metering trustworthy enough for calibration prep |

**Still human:** Cursor key confirmation, Anthropic key, Groq rotation, tower online, optional dedicated `sk-mr-*` master key.

**Next phase:** Phase 1 catalog (`models_catalog.yaml`) — not Console yet.

# ModelRouter cycles

**Repo-local slash commands** live in `.cursor/commands/`. When you run `/cycle`, `/ship`, or any alias in this workspace, Cursor uses these prompts instead of your global `~/Dev/prompts/cycles.md` copies.

Use these between work bursts. The aim is not perfection — it is a **living homelab gateway** that stays shippable: one LAN front door, policy presets, keys on kc-mini, honest ops.

---

## What you are steering

**ModelRouter** is a self-hosted LiteLLM gateway — OpenAI-compatible at `http://127.0.0.1:3000` (laptop) and your LAN gateway URL (see `config/hosts.yaml`). Clients ask for **presets** (`hermes-fast`, `cheap`, `code`, …), not vendor model names.

| Host | Role |
|------|------|
| **kc-mini** | Gateway, provider keys, `make deploy-mini` target |
| **kc-tower** | Hermes / Kalshi / coinbot — gateway client only |
| **laptop** | Dev, Cursor, Keys widget, push to mini |

North star: `docs/HOMELAB_GOALS.md`. Product path: `docs/PRODUCT_VISION.md`. Wires first: `docs/CLEAN_WIRES.md`.

**Current phase:** Phase 0 largely done; Phase 1 (catalog & calibration) in progress. Iteration log: `docs/iterations/`.

---

## Operating covenant

- **Ship small.** One iteration, one clear goal. Prefer a five-line fix over a refactor.
- **Stay light.** ~1 MB git tree; no databases in native homelab mode unless intentional.
- **Preserve unrelated work.** Do not stomp the user's in-flight changes.
- **Never commit secrets.** `.env`, `secrets.yaml`, `data/CORE_APIS.md`, raw keys, pid noise, `.venv`.
- **Do not rotate `MODELROUTER_MASTER_KEY` casually.** Keep `crsr_*` for Cursor unless the human explicitly wants to rewire Cursor.
- **SSOT discipline.** Presets: `config/includes/policy_presets.yaml`. Catalog: `config/models_catalog.yaml`. Sync caps: `make sync-preset-tokens`.
- **If the repo is already healthy,** tighten docs, reduce drift, or add validation — do not invent churn.

---

## Roles (same every command)

| Role | Duty |
|------|------|
| **Lead** | Read repo state, `docs/iterations/`, `docs/ITERATION_REVIEW.md`, `docs/COMMITTEE_REVIEW.md`; pick priorities. |
| **Builder** | Smallest safe change that moves the needle. |
| **Reviewer** | Regressions, overreach, secret leakage, config drift. |
| **Validator** | Run the right `make` targets; gateway/mini health when routing or deploy touched. |
| **Closer** | Summarize, version bump if cycle-complete, commit/push/deploy only when appropriate. |

---

## Slash commands

| Command | Purpose |
|---------|---------|
| `/cycle` or `/i5` | **Full global cycle** — cleanup → deepclean → test/lint → five iterations → cleanship → ship |
| `/cleanup` | Phase 1 only — practical hygiene |
| `/deepclean` | Phase 2 only — drift hunt |
| `/cleanship` | Phase 3 or 5 only — validate + hand-off ready |
| `/ship` | Phase 6 only — verify, commit, push, `deploy-mini` |

`/cycle` runs all of the above in order. Use individual commands when you only need one phase.

---

## `/cycle` and `/i5` — full global cycle

**Goal:** One complete pass from messy → clean → improved → validated → shipped. Advance ModelRouter in five bounded iterations without bloating the repo. Capstone at **X.5** (e.g. v3.5.0) updates `VERSION` + `CHANGELOG`.

### Pipeline (execute in order)

| Phase | Command | What happens |
|-------|---------|--------------|
| **0** | Orient | Read `VERSION`, `git status`, iteration docs, name next five IDs |
| **1** | `/cleanup` | Hygiene — junk, stale docs, URL/preset drift |
| **2** | `/deepclean` | Drift — SSOT, ops scripts, widget, cheap reliability fixes |
| **3** | `/cleanship` | Baseline `make test` + `make lint` + preset/catalog checks |
| **4** | Five iterations | Security → reliability → correctness → ops → docs; validate each |
| **5** | `/cleanship` | Post-iteration full validation + doc alignment |
| **6** | `/ship` | `git` review, commit (if asked), push, `make deploy-mini` when gateway changed |

Skip a phase only when there is genuinely nothing to do — say so in the close-out report.

### Iteration priority (Phase 4)

1. **Security** — no secret commits; widget/gateway auth; key exposure; master/salt policy
2. **Reliability** — daemon, pidfile, health on `0.0.0.0`, `stop.sh`, deploy races, mini reachability
3. **Correctness** — preset SSOT, catalog sync, route hints, fallbacks, tests
4. **Operability** — doctor, homelab-status, deploy-mini, tower client env, core-apis
5. **Documentation** — iterations README, CHANGELOG, HOMELAB_GOALS human backlog
6. **Cleanup** — only if nothing above needs attention

### Output contract

Report **every phase** (even "nothing needed"):

- Orient → Cleanup → Deepclean → Baseline checks
- Five iterations: goal → change → validation each
- Final cleanship → Ship status
- Health table · deferred human backlog · **shipped / ready to ship / continue**

### How to think

- The gateway is infrastructure, not a canvas. Every change should make **finish the homelab product** easier.
- **Fail down, not up** — fallbacks go cheaper/local before expensive.
- OpenRouter stays **stubbed** unless explicitly requested.
- Cost discipline: would a cheaper preset or non-LLM tool already solve it?

---

## Validation matrix

Use in Phases 3, 4 (per iteration), 5, and 6:

| Change type | Checks |
|-------------|--------|
| Shell, YAML, config | `make lint` |
| Python, routing, presets, widget | `make test` |
| Gateway, daemon, bind, deploy | `make restart` → `make health` → `make doctor` |
| Homelab posture | `make homelab-status` or `make remote-health` |
| Keys, routing, model selection | `make cost-review`; never log full keys |
| Catalog / preset caps | `make check-catalog`, `make check-presets`, `make sync-preset-tokens` |
| Private API inventory | `make core-apis` (gitignored output) |
| Shipped to mini | `make deploy-mini` after commit when gateway or ops scripts changed |

---

## `/cleanup` (Phase 1)

Practical hygiene. Remove junk, align short docs with reality, run relevant checks. Do not delete config you do not understand — document instead.

---

## `/deepclean` (Phase 2)

Deeper pass: duplicated YAML, stale comments, `policy_presets` vs gateway YAML drift, scripts that no longer match `hosts.yaml` URLs, cache artifacts. Fix root cause when cheap.

---

## `/cleanship` (Phase 3 or 5)

Baseline (before iterations) or final (after): update docs that lie → `make test` + `make lint` + preset/catalog checks → fix regressions → tree ready for `/ship`.

---

## `/ship` (Phase 6)

Finish the burst.

1. `git status` / `git diff` — no secrets, no `data/CORE_APIS.md`
2. `make test` && `make lint`
3. `make doctor` or `make homelab-status` if ops/gateway touched
4. Commit with accurate message; push if on a feature branch
5. **`make deploy-mini`** when `config/`, `scripts/`, `modelrouter/`, or `tokens/` changed on mini

---

## Human backlog (do not auto-fix silently)

- Confirm Cursor base URL → ModelRouter, not direct OpenAI
- `make push-client-env-tower` when kc-tower SSH works
- `ANTHROPIC_API_KEY` on mini when available
- Groq key rotation if previously exposed
- Distinct `LITELLM_SALT_KEY` before Docker/Postgres

---

*Source: evolved from `~/Dev/prompts/cycles.md` for ModelRouter homelab context.*

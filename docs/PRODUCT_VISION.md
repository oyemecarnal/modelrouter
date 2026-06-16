# ModelRouter product vision

**Status:** Homelab core today → deliberate path to **purchase / SaaS** product.  
**Pace:** Do not rush. Each phase earns the next with clean wires and measured usage.

---

## One-sentence pitch

**ModelRouter is the control plane for AI on your machines** — one API, one key store, policy-based models, honest quota/cost view, and optional connectors — so individuals and teams stop tangling keys across apps.

---

## Why clean wires come first

You cannot sell or calibrate what you cannot measure. Phase 0 (now) is **untangling**:

- All LLM clients → single gateway (`docs/CLEAN_WIRES.md`)
- New `MODELROUTER_MASTER_KEY` per deployment (not recycled from Cursor/OpenAI)
- Per-project virtual keys for attribution
- Provider secrets only on the gateway host

Only then: token budgets, context limits per preset, cross-platform sync.

---

## Product layers (long-term)

```
┌─────────────────────────────────────────────────────────┐
│  ModelRouter Console (Web UI) — future                  │
│  Model grid · Add provider · Quota · Project keys     │
└──────────────────────────┬──────────────────────────────┘
┌──────────────────────────▼──────────────────────────────┐
│  Harness layer                                          │
│  · machine-scraper (safe API discovery)                 │
│  · connector framework (OAuth / “login at provider”)    │
│  · policy engine (presets, fallbacks, cost-review)      │
└──────────────────────────┬──────────────────────────────┘
┌──────────────────────────▼──────────────────────────────┐
│  Gateway (LiteLLM today) — OpenAI-compatible /v1        │
└──────────────────────────┬──────────────────────────────┘
┌──────────────────────────▼──────────────────────────────┐
│  Providers + local (Ollama)                             │
└─────────────────────────────────────────────────────────┘
```

### Console UI (future, not v1.5)

- **Model choice grid** — click preset or provider model; see cost tier, context window, status (green/gray/red)
- **Add new** — opens provider signup; later: **connector** completes OAuth and stores key in vault (never in chat)
- **Projects** — Hermes, Kalshi, Cursor each get a row: preset, spend, last call
- **Calibration** — sliders or caps: max tokens per preset, per day, per project

Homelab today: **Keys widget** is the seed; Console replaces/extends it when ready.

### Harnesses (series, not one blob)

| Harness | Role | Homelab today |
|---------|------|----------------|
| **Gateway harness** | Start, health, deploy, doctor | `scripts/`, Makefile |
| **Policy harness** | Presets, route hints, fallbacks | `route_policy.py`, YAML |
| **Inventory harness** | Allowed-folder API + crypto surface scan (masked) | `make inventory`, `machine_inventory.py` |
| **Connector harness** | Provider login → vault | *Future* — start with manual `.env` + 1Password |
| **Meter harness** | Tokens, spend, context audit | Logs + widget; → Postgres later |

### Connector vision (high-level permission)

Not “full machine admin.” Staged consent:

1. **Read-only scan** — list configured APIs (masked), free-tier hints
2. **Per-provider connect** — user logs in at vendor site; connector stores refresh token / API key in 1Password or local vault
3. **Optional machine scope** — “scan `~/dev` for `.env`” with explicit paths (already partially in tokens)

Avoid a single god-mode connector until security model is designed (Business tier).

---

## Tiers (commercial model sketch)

| Tier | Buyer | Includes | Why not rush |
|------|--------|----------|--------------|
| **Personal** | Homelab / solo dev | Gateway + widget + presets + 1 machine | **You are here** — prove wires + policy |
| **Pro** | Power user / small studio | Multi-machine sync, Console UI, project keys + caps, MCP | Needs stable daemon + UI MVP |
| **Business** | Team / agency | SSO, audit log, per-seat keys, spend policies, connector admin, support | Needs Postgres, compliance story, billing |

**Pricing shape (ideas only):** Personal one-time or cheap annual; Pro subscription; Business per-seat + usage markup or flat team fee.

**SaaS vs purchase:** Homelab = **purchase / self-host** first (trust, keys stay home). Optional **hosted control plane** later (sync config, not proxy traffic) for Pro/Business.

---

## Phased roadmap (don’t skip phases)

### Phase 0 — Clean wires (complete → 3.7)

- [x] Fail-closed startup; project key refresh on rotate
- [x] `config/client.env.example` for tower (no provider keys)
- [x] `docs/CLEAN_WIRES.md` migration guide (human items flagged)
- [x] Daemon reliable enough to trust metering (pid + stop + health bind)
- [x] All clients on gateway only — Cursor, tower Tailscale, mini canonical keys (`docs/HOMELAB_GOALS.md`)

### Phase 1 — Catalog & calibration (complete → 3.7)

- [x] `config/models_catalog.yaml` — context window, cost tier, presets (Phase 1 SSOT)
- [x] `make check-catalog` / `scripts/check_catalog.py` — drift check in `make test`
- [x] Console MVP: static grid in widget — `docs/CONSOLE_SPEC.md`, **Console** section (`consoleGrid`)
- [x] Per-preset max tokens enforced in LiteLLM config (`make sync-preset-tokens`, `check_catalog`)
- [x] Context window SSOT + selection guide — `docs/CONTEXT_GUIDE.md`; `check_catalog` validates `context_window`
- [x] Log metering in ops — `make usage-rollup` in `homelab-status` and `doctor` next steps

### Phase 2 — Connector MVP (3.8+ → 3.12)

- [x] Connector spec — `docs/CONNECTOR_SPEC.md` (security model, vault rules)
- [x] Paste-key connectors — Groq, Anthropic, OpenAI, Mistral (`config/connectors.yaml`, `make connect-provider`)
- [x] Registry-driven receiver LEDs — `homelab_status` reads `connectors.yaml`
- [x] Tower wire audit — `make audit-tower-wires`, `make clean-tower-wires`
- [x] Keys never touch repo; vault write only *(OAuth deferred)*
- [ ] “Add new” button → provider page → return → key stored *(widget UI deferred)*

### Phase 3 — Pro product (4.x)

- [ ] Multi-host dashboard (laptop + mini + tower status)
- [ ] Project spend caps enforcement (virtual keys + DB)
- [ ] Installer / signed macOS app (?)

### Phase 4 — Business tier (5.x+)

- [ ] Team admin, audit, SSO
- [ ] Approved connector list for org
- [ ] SLA, support, invoicing

---

## What we explicitly defer

- OpenRouter as default (stub stays)
- Full “connect everything” OAuth monster
- Billing integration before metering is trustworthy
- Replacing LiteLLM before gateway is boring-reliable

---

## Homelab → product bridge

| Homelab asset | Product feature |
|---------------|-----------------|
| `tokens/` widget | Console quota panel |
| `make cost-review` | Pro “should I use something else?” |
| `config/projects.yaml` | Business project admin |
| `route_policy.py` | Auto downshift / calibration engine |
| `mcp_server.py` | Agent integrator for Pro+ |
| `config/hosts.yaml` | Multi-machine fleet view |

---

## Standing question (every phase)

> Is there already a better, cheaper tool — or must this be ModelRouter?

Run `make cost-review`. If the answer is “use grep not GPT,” the product should **say that**, not route the call.

---

## Next doc when ready

- `docs/CONSOLE_SPEC.md` — wireframes + API for model grid (Phase 1) ✓
- `docs/CONTEXT_GUIDE.md` — preset selection by context window (Phase 1) ✓
- `docs/CONNECTOR_SPEC.md` — OAuth scopes + vault layout (Phase 2) ✓ MVP
- `docs/POSITIONING.md` — market wedge vs LiteLLM / Portkey / key wallets ✓
- `docs/LANDING.md` — Personal tier landing stub ✓

Phase 0/1 complete at **v3.7.0**. Phase 2 connectors through **v3.18.0** (9 paste-key flows, Personal tarball, tower guides). OAuth and widget paste UI next.

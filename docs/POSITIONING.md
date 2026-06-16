# ModelRouter positioning

**One line:** Self-hosted AI control plane — vault keys on your gateway, route by policy, see connectivity on a receiver-style console.

**Audience today:** Homelab / solo dev / small studio who refuse to spray API keys across `.env` files and want one metered front door.

**Not:** A crypto wallet. Not enterprise Portkey. Not a browser-only key extension.

---

## The problem we solve

| Pain | ModelRouter answer |
|------|-------------------|
| Keys in `.zshrc`, tower, laptop, Cursor, bots | One vault on **kc-mini**; clients use gateway + presets |
| Direct OpenAI/Groq calls bypass metering | Single `/v1` surface; `make usage-rollup` |
| “Is Groq/mini/tower up?” | Widget **receiver bar** — paths, API keys, network LEDs |
| Paste key → forget where it landed | `make connect-groq` / `make connect-anthropic` → validate → push → restart |
| Don’t know what’s on disk | `make inventory` / `make keys-audit` (masked) |

---

## Competitive map (2026)

| Product | What it is | Gap ModelRouter fills |
|---------|------------|------------------------|
| **LiteLLM** | OSS gateway proxy | No homelab UX, inventory, or connector paste flows |
| **Portkey / Kong AI** | Enterprise SaaS control plane | Self-host, no per-seat SaaS, homelab-first |
| **OpenRouter** | Managed multi-model API | You don’t own keys or policy on your LAN |
| **Lockbox / API Key Wallet** | Browser vault + autofill | No routing, metering, or gateway on your mini |
| **1Password** | Enterprise secrets + agent MCP | Not preset policy, not LLM gateway, not receiver ops UI |

**Wedge:** *Purchase/self-host control plane for individuals* — between “raw LiteLLM in a venv” and “Portkey for the whole company.”

---

## Product shape (Swiss Army — one spine, many blades)

```
Receiver Console (widget)     ← see connectivity, quotas, presets
        │
Harness: inventory · connector · policy · meter
        │
Gateway (LiteLLM on kc-mini)  ← single /v1, keys stay here
        │
Providers + Ollama
```

| Blade | Homelab today | Pro (later) |
|-------|---------------|-------------|
| **Scan** | `make inventory`, `make keys-audit` | Scheduled fleet scan |
| **Store** | `connect-*`, `env_store`, mini `.env` | 1Password Connect, rotation |
| **Route** | Presets, fallbacks, `route_policy` | Project caps, virtual keys + DB |
| **Meter** | Logs, widget, `usage-rollup` | Dashboard, alerts |
| **See** | Receiver LEDs, 5 theme presets | Standalone Console app |

Crypto keys: **inventory only** (locations, masked) — not custody. Keeps AI and Web3 adjacent without “crypto wallet” confusion.

---

## Tiers (from `docs/PRODUCT_VISION.md`)

| Tier | Buyer | Price shape (idea) |
|------|-------|-------------------|
| **Personal** | Homelab / you | One-time or cheap annual — **you are here** |
| **Pro** | Power user / studio | Subscription — multi-host, caps, installer |
| **Business** | Team | Per-seat + governance — defer |

**Personal SKU story:** Pay once, keys stay home, Cursor + tower + bots through one gateway, receiver shows truth.

---

## What we claim (honest)

- Policy-based routing, not vendor lock-in per app  
- Self-hosted gateway on your hardware  
- Masked inventory — find keys, don’t exfiltrate them  
- Paste-key connectors with validation (7 registry entries — Groq through Together)  
- Stereo-receiver ops UI — distinctive, memorable  

## What we do not claim (yet)

- SOC 2 / HIPAA / SSO  
- OAuth “connect everything”  
- Billing / invoicing  
- Replacing 1Password for all secrets  
- Crypto custody or payments  

---

## Brand notes

- **Name:** ModelRouter (keep)  
- **Metaphor:** Hi-fi receiver — connectivity lamps, preset themes (Marantz, McIntosh, Classic R/G)  
- **Avoid:** “Crypto wallet for APIs” in headline — use “vault” or “connector”  
- **Tagline candidates:**  
  - *Route models. Vault keys. See everything.*  
  - *The control plane for AI on your machines.*

---

## Wiring checklist (human + agent)

**Done enough to demo**

- [x] Gateway on kc-mini, tower Tailscale, Cursor path  
- [x] Paste-key connectors — 9 registry entries (`config/connectors.yaml`)  
- [x] Widget paste modal + receiver hints (`make ensure-gateway`)  
- [x] Tower wire audit/strip — coinbot Option A (`docs/WHY_MODELROUTER.md`)  
- [x] `docs/ENV.md`, `docs/LANDING.md`, `make ship-check`  
- [ ] **v3.22.0** shipped on `main` (local ready — run `/ship`)

**Next wires (in order)**

1. **`/ship v3.22.0`** + `make deploy-mini`  
2. **`make daemon-enable`** on laptop — `docs/LAPTOP_DAEMON.md`  
3. **Personal tier sale** — tarball + Gumroad when interviews say yes  
4. **OAuth exchange** — Phase 3 (`docs/OAUTH_CONNECTOR_SPEC.md`)

---

## Standing question

> Would you pay **$49–99 once** for self-hosted ModelRouter vs **$49/mo** for Portkey?

Ask 5 power users before building Business tier. Homelab proves the spine; interviews prove the price.

---

## Related docs

- `docs/PRODUCT_VISION.md` — phases and tiers  
- `docs/CONNECTOR_SPEC.md` — paste-key security  
- `docs/CLEAN_WIRES.md` — migration  
- `docs/ENV.md` — variables  
- `config/connectors.yaml` — connector registry  

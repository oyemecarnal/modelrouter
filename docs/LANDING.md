# ModelRouter — Personal tier (landing stub)

**Tagline:** *Route models. Vault keys. See everything.*

Self-hosted AI control plane for homelab and solo dev. One gateway on your hardware, policy presets for every client, and a receiver-style console that shows what's actually connected.

Full positioning: [docs/POSITIONING.md](POSITIONING.md)

---

## Who it's for

- You run **Cursor**, tower agents, or bots and want **one** OpenAI-compatible endpoint
- You're tired of provider keys scattered across laptop, tower, and shell rc files
- You want **metering and fallbacks** without Portkey's per-seat SaaS bill

---

## What you get (Personal)

| Included | Notes |
|----------|--------|
| LiteLLM gateway + policy presets | `hermes-fast`, `hermes-smart`, `cheap`, `code`, … |
| Paste-key connectors | Groq, Anthropic, OpenAI, Mistral → mini vault |
| Receiver widget | Paths, API keys, network LEDs + 5 theme presets |
| Homelab ops | `make doctor`, `deploy-mini`, `usage-rollup`, tower wire audit |
| Docs + tarball | Self-host on kc-mini (or any Mac/Linux you control) |

**Not included (yet):** OAuth connectors, team SSO, hosted billing, crypto custody.

---

## Price shape (idea — validate with users)

| Option | Target |
|--------|--------|
| **$49–99 once** | Personal — tarball + docs + email support |
| **$19/mo** | Pro — multi-host installer, caps, alerts *(later)* |

> Standing question: would you pay once for self-hosted vs **$49/mo** for Portkey?

---

## Quick start

```bash
git clone <repo> ~/dev/modelrouter
cd ~/dev/modelrouter
make install
cp .env.example .env          # or make connect-groq / connect-anthropic
make deploy-mini              # production gateway on your mini
make homelab-status
```

Cursor: base URL `http://127.0.0.1:3000` (laptop) or mini LAN URL.  
Tower: `make push-client-env-tower` — gateway auth only, no provider keys.

---

## Purchase / download

**Status:** Not for sale yet — homelab dogfood phase. Codebase **v3.18.0** on `main` (9 paste-key connectors).

When ready:

1. Tagged release tarball — `make package-personal` → `dist/modelrouter-v3.18.0-personal.tar.gz`
2. Optional Gumroad / GitHub Sponsors link here
3. License: see repository `LICENSE`

Contact / interest: open a GitHub issue with label `personal-tier`.

---

## Related

- [HOMELAB_GOALS.md](HOMELAB_GOALS.md) — spine checklist  
- [ENV.md](ENV.md) — variables and connect commands  
- [CLEAN_WIRES.md](CLEAN_WIRES.md) — key namespace rules  
- [PRODUCT_VISION.md](PRODUCT_VISION.md) — phases and tiers  

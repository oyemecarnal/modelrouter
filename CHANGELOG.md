# Changelog

## [3.37.0] — 2026-06-17 (Cycle 37 — rotate simulate, connector stash-alt, deploy)

### Added
- **`make vault-rotate-simulate`** — synthetic 429 → rotate hint + export dry-run (`PROVIDER=groq`, `CLEANUP=1`)
- **`connect-mistral --stash-alt`** / **`connect-anthropic --stash-alt`** — parity with Groq rotate flow

### Changed
- Connectors push `__ALT_1` when present (Mistral, Anthropic)
- `vault-rotate-drill` runs groq simulate with `--cleanup`
- Mini deployed to **v3.37.0**

## [3.36.0] — 2026-06-17 (Cycle 36 — alts live, dedupe env, smoke-routes)

### Added
- **`make dedupe-env`** / **`dedupe-env-apply`** — drop duplicate `.env` keys (keeps last; no value print)
- **`make smoke-routes`** — hermes-fast + hermes-smart smoke in one pass
- **`make vault-bootstrap-alts-restart`** — bootstrap alts + restart mini

### Changed
- Homelab **alt_keys** hint — partial shuffle messaging (e.g. 3/4)
- **`make enable-auto-rotate-mini-enable`** — write ROTATE+RESTART gates on kc-mini

### Ops (human)
- 3/4 providers alt-shuffle live (Groq, Anthropic, OpenAI); Mistral pending

## [3.35.0] — 2026-06-17 (Groq cycle — stash-alt + smoke-hermes-fast)

### Added
- **`make smoke-hermes-fast`** — Groq route smoke via kc-mini gateway
- **`connect-groq --stash-alt`** — move previous primary → `GROQ_API_KEY__ALT_1` on rotate

### Changed
- `connect-groq` pushes `GROQ_API_KEY__ALT_1` when present; auto `vault ingest-alts` after stash

## [3.34.0] — 2026-06-12 (Cycle 34 — ingest alts, bootstrap, mini auto-rotate)

### Added
- **`vault ingest-alts`** — merge local `.env` `__ALT_N` lines into vault (no secret print)
- **`make vault-bootstrap-alts`** — ingest → export → push alts (+ optional `--restart-mini`)
- **`make enable-auto-rotate-mini`** — set `MODELROUTER_AUTO_VAULT_ROTATE/RESTART=1` on kc-mini (not PUSH)

### Changed
- `connect-alt-key` — auto-ingests pasted alt into vault
- `vault-rotate-drill` — reports mini auto-rotate gate status
- `test.sh` — ingest + 429 `record_rate_limit` simulation with 2 keys

## [3.33.0] — 2026-06-12 (Cycle 33 — alt paste, rotate drill, ALTS LED)

### Added
- **`make connect-alt-key`** — paste `VAR__ALT_N` into `.env` + optional `push-alt-keys-mini`
- **`make vault-rotate-drill`** — dry-run 429 rotate pipeline readiness (no secrets)
- **`make vault-sync-alts-restart`** — export, push alts, restart mini gateway
- **Widget ALTS LED** — vault multi-key readiness + `alt_keys` hint in homelab status

### Changed
- `vault_alt_readiness()` — counts enabled keys per alt-routed provider
- `doctor` next-steps — rotate drill + connect-alt-key paths

## [3.32.0] — 2026-06-12 (Cycle 32 — alt scrape ingest + vault sync alts)

### Added
- **Vault `__ALT_N` scrape** — ingests `GROQ_API_KEY__ALT_1` etc. as second keys under base `env_var`
- **`make vault-sync-alts`** — export vault → laptop `.env` → `push-alt-keys-mini` (+ optional `--restart-mini`)
- **`make check-alt-keys-mini`** — remote mini `.env` alt-key audit (names only)

### Changed
- `key_vault` laptop scrape reads `env_files` for explicit `__ALT_N` lines
- `test.sh` — alt normalize/export unit check + mini alt audit (warn-only)

## [3.31.0] — 2026-06-12 (Cycle 31 — mini bootstrap + alt key ops)

### Added
- **`make bootstrap-mini`** — deploy + `daemon-enable-mini` + `push-alt-keys-mini`
- **`make check-alt-keys`** — config vs `.env` alt key audit (never prints values)
- **`make push-alt-keys-mini`** — sync `__ALT_N` vars laptop → kc-mini
- **`make daemon-enable-mini`** — launchd bootstrap on kc-mini over SSH

### Changed
- `smoke-hermes-smart` — `/v1/models` hermes-smart check + alt-key hints
- `deploy-to-mini` — points at `make daemon-enable-mini`
- `daemon-enable` / `daemon-disable` — avoid `UID` (readonly in `/bin/sh` on macOS)
- `test.sh` — warn-only alt key check

## [3.30.0] — 2026-06-12 (Cycle 30 — Anthropic alts + hint clear + auto push)

### Added
- **Anthropic alt routes** — `ANTHROPIC_API_KEY__ALT_1` on `hermes-smart` and `review`
- **Rotate hint clear** — `mark_rotate_hint_applied()` after `vault-rotate-push`; ROTATE LED hides applied hints
- **Opt-in auto push** — `MODELROUTER_AUTO_VAULT_PUSH=1` runs `vault-rotate-push` after auto-export

### Changed
- `remote-health` — mini probe tries all URLs silently, one ok/down line
- `logging_callback` — `rotate_push` event when auto-push runs

## [3.29.0] — 2026-06-12 (Cycle 29 — OpenAI/Mistral alts + rotate LED + auto restart)

### Added
- **OpenAI/Mistral alt routes** — `OPENAI_API_KEY__ALT_1` / `MISTRAL_API_KEY__ALT_1` on `hermes-smart`, `code`, `hermes-fast`, `cheap`
- **Widget ROTATE LED** — homelab receiver bar shows pending 429 rotate hints
- **Opt-in auto restart** — `MODELROUTER_AUTO_VAULT_RESTART=1` runs `make restart` after auto-export

### Changed
- `homelab_status` — `key_rotate` hint with `vault-rotate-push` fix path
- `logging_callback` — `rotate_restart` event when auto-restart runs

## [3.28.0] — 2026-06-12 (Cycle 28 — alt Groq routes + auto rotate + push)

### Added
- **Groq alt deployments** — `hermes-fast` / `cheap` use `GROQ_API_KEY__ALT_1` via `simple-shuffle`
- **Opt-in auto rotate** — `MODELROUTER_AUTO_VAULT_ROTATE=1` exports `.env` on 429 (gateway host only)
- **`make vault-rotate-push`** — rotate export + push rotated keys to kc-mini

### Changed
- `logging_callback` — optional `rotate_export` event when auto-rotate enabled
- Tests: `maybe_auto_rotate_export` gate

## [3.27.0] — 2026-06-12 (Cycle 27 — Tangem ETH + rotate export + daemon fix)

### Added
- **ETH balance RPC fallback** — public JSON-RPC when `ETHERSCAN_API_KEY` missing (Tangem watch wallets)
- **`make vault-rotate-export`** — apply last 429 rotate hint → `.env` merge
- Widget fetch uses **modelrouter `.venv`** (fixes SSL cert errors on laptop)
- `daemon-enable` / `daemon-disable` — `launchctl bootstrap` / `bootout` for modern macOS

### Changed
- `fetch_ethereum_balance` — Etherscan first, Cloudflare RPC fallback
- Tests: Ethereum RPC, vault rotate export, Tangem preset sync when env set

## [3.26.0] — 2026-06-12 (Cycle 26 — 429 rotate + vault widget + OAuth exchange)

### Added
- **429 key rotation hints** — `record_rate_limit()` on gateway failure; `data/key_rotate_hints.json`
- **Widget key vault panel** — masked entries with enable/disable toggle (`POST /vault/toggle`)
- **OAuth Google exchange stub** — `modelrouter/oauth_exchange.py` behind `OAUTH_EXCHANGE=1`; state validation in callback listener
- Doctor row for recent rate-limit rotate hints

### Changed
- `logging_callback` — emits `rotate_hint` on 429 failures
- `fetch_usage` snapshot includes `keyVault` (masked)
- `oauth_callback_stub` — generates dev state; attempts exchange when code present

## [3.25.0] — 2026-06-12 (Cycle 25 — vault export guard + route key hints)

### Added
- **Vault export deny** — `export_deny_vars` / `export_deny_prefixes` block sensitive vars from `.env` merge
- **Route key hints** — `route_policy` writes `key_hints` (vault fingerprint) when quota pressure is high and alternates exist
- `make doctor-fix` — one-shot gateway restart companion to `make doctor`
- Tangem watch-wallet placeholders in `tokens/.env.local.example`

### Changed
- `export_env` — skips blocked vars; tests for export deny + route hints

## [3.24.0] — 2026-06-16 (Cycle 24 — widget reliability + vault ops)

### Added
- Equity **fetch timeout** in widget (`fetch_timeout_seconds`) — stale cache fallback when Kraken/live brokers hang
- **Key vault** hints in homelab receiver bar + doctor vault row
- Tests: vault masked export guard, equity bounded fetch helper

### Changed
- `fetch_usage` — equity via `_fetch_equity_safe` (90s default) instead of unbounded live fetch
- `doctor` — vault status + next-step commands; fixed gateway hint indentation

## [3.23.0] — 2026-06-16 (Cycle 23 — portfolio equity + key vault + themes)

### Added
- **Network key vault** — `modelrouter/key_vault.py`, `config/key_vault.yaml`, `make vault-scrape` / `vault-scrape-collect` / `vault-export`
- `docs/KEY_VAULT.md` — permissions, multi-key per service, routing-aware select
- **Portfolio equity** — Kraken/Coinbase broker routes, Kalshi live balance (`equity_kalshi.py`), cold-wallet USD (`price_oracle.py`)
- **Widget themes** — 11 receiver presets, discreet header Theme dropdown; `docs/THEME_DESIGN.md`
- Tangem wallet presets via `TANGEM_*` env or `wallets.presets` in config

### Changed
- `fetch_equity` — per-broker SSH routes, unified portfolio total + breakdown
- `equity_remote_runner` — Fernet-only encrypted-key detect; full multi-asset USD pricing
- `fetch_wallets` — CoinGecko USD valuation; `include_in_equity` rolls into portfolio
- Widget — Portfolio section (exchange + prediction + cold wallet cards)

## [3.22.0] — 2026-06-16 (Cycle 22 — ship gate + ensure-gateway + OAuth stub)

### Added
- `make ensure-gateway` — restart laptop gateway if healthcheck fails
- `make ship-check` — pre-ship validation (test, lint, VERSION/CHANGELOG, tower audit)
- `make oauth-start` — Phase 3 OAuth stub + dev callback listener (`OAUTH_STUB_LISTEN=1`)
- `docs/SHIP_CHECKLIST.md` — human + automated ship gate

### Changed
- Gateway-down hints → `make ensure-gateway` (homelab_status, homelab-status, cost-review, doctor)

## [3.21.0] — 2026-06-16 (Cycle 21 — OAuth draft + gateway hints)

### Added
- `docs/OAUTH_CONNECTOR_SPEC.md` — Phase 3 OAuth draft (security, flow, acceptance criteria)
- `homelab_status` `hints` — laptop/mini gateway fix commands for widget receiver bar

### Changed
- Widget provider modal — optional **Push to mini** / **Restart gateway** checkboxes
- `homelab-status`, `cost-review` — gateway-down fix lines (`make restart` / `make daemon-enable`)
- `OAUTH_CONNECTOR_STUB.md` — links to OAuth spec

## [3.20.0] — 2026-06-16 (Cycle 20 — paste modal + tower strip + doctor)

### Added
- Widget **＋ Provider** paste modal — `/connectors/paste` validates, saves `.env`, pushes to mini
- `make strip-tower-llm-keys` — remove stray LLM keys from tower `~/dev/*/.env*` (Option A)
- `tokens/scripts/connector_paste.py` — shared paste-key logic for widget

### Changed
- `audit-tower-wires` — scans `.env.*` (e.g. `.env.cursor`); skips `*.bak*` backups
- `doctor` — prominent fix block when gateway is down (`make restart` / `make daemon-enable`)
- `homelab_status` — `registryConnectors` includes `env` + prefix for widget modal

## [3.19.0] — 2026-06-15 (Cycle 19 — why doc + wire exceptions)

### Added
- `docs/WHY_MODELROUTER.md` — plain-English value story (gateway vs direct keys, coinbot)
- `config/wire_exceptions.yaml` — documented tower audit exemptions
- `docs/OAUTH_CONNECTOR_STUB.md` — Phase 3 OAuth placeholder

### Changed
- `audit-tower-wires` — respects `wire_exceptions.yaml`; links WHY doc
- `README`, `HOMELAB_GOALS`, `CLEAN_WIRES` — point at WHY doc

## [3.18.0] — 2026-06-15 (Cycle 18 — capstone: 9 connectors + Personal pack)

### Changed
- `README`, `LANDING`, `PRODUCT_VISION` — v3.18.0, `make package-personal`
- Cycles 14–18 bundle ready to ship (origin at v3.13.0)

## [3.17.0] — 2026-06-15 (Cycle 17 — tower stray-key guide)

### Added
- `make guide-tower-strays` — audit + human cleanup steps (coinbot pattern)

### Changed
- `homelab-status` — tower row links guide command

## [3.16.0] — 2026-06-15 (Cycle 16 — Cohere connector)

### Added
- `make connect-cohere` — ninth registry paste-key connector

## [3.15.0] — 2026-06-15 (Cycle 15 — Fireworks + Personal tarball)

### Added
- `make connect-fireworks` — paste `fw_…` → mini
- `make package-personal` — tarball for Personal tier (`dist/modelrouter-*-personal.tar.gz`)

### Changed
- Registry: 8 paste-key connectors

## [3.14.0] — 2026-06-15 (Cycle 14 — DeepSeek/Together + Add Provider + daemon docs)

### Added
- `make connect-deepseek`, `make connect-together` — paste-key connectors (7 registry entries)
- `docs/LAPTOP_DAEMON.md` — launchd auto-start for stable Cursor gateway
- Widget **＋ Provider** menu — registry signup links + `make connect-*` hints

### Changed
- `homelab_status` — `registryConnectors` for widget menu
- `env_store` — DeepSeek (`sk-…`) and Together key validation
- `push-env-mini` — includes `DEEPSEEK_API_KEY`, `TOGETHER_API_KEY`
- `docs/CURSOR_WIRING.md` — points at laptop daemon doc

## [3.13.0] — 2026-06-15 (Cycle 13 — Google connector + widget signup links)

### Added
- `make connect-google` — paste `AIza…` → `.env` → mini (`GEMINI_API_KEY` alias when unset)
- `docs/TOWER_CLEANUP.md` — tower agent `.env` cleanup (coinbot pattern)
- Widget receiver — signup links for missing registry connectors (`connectors.yaml`)

### Changed
- `homelab_status` — registry LEDs include `signup` URLs; Google moved into registry
- `env_store` — `GOOGLE_API_KEY` validation (`AIza…`)
- `audit-tower-wires` — coinbot-specific cleanup hint
- `test.sh` — Google validation + signup URL smoke

## [3.12.0] — 2026-06-15 (Cycle 12 — landing stub + Mistral + registry LEDs)

### Added
- `docs/LANDING.md` — Personal tier landing / purchase stub
- `make connect-mistral` — paste Mistral key → mini
- `make clean-tower-wires` — push tower `client.env` + re-audit

### Changed
- `homelab_status` — API KEY row driven by `config/connectors.yaml`
- `audit-tower-wires` — skip `OPENAI_API_KEY` in tower `client.env` (gateway shim)
- `test.sh` — Mistral validation + registry LED smoke (4+ paste-key LEDs)

### Changed (deepclean)
- `docs/PRODUCT_VISION.md`, `CONNECTOR_SPEC.md` — version and Phase 2 status sync
- `README` — dedupe `daemon-enable`; connector command labels
- `tokens/README.md` — fix broken Files table
- `check-key-hygiene` — mini checks include OpenAI + Mistral

## [3.11.0] — 2026-06-15 (Cycle 11 — tower audit + OpenAI connector)

### Added
- `make audit-tower-wires` — scan kc-tower for stray provider keys (no values printed)
- `make connect-openai` — paste `sk-…` → `.env` → `push-env-mini` → mini restart
- OpenAI entry in `config/connectors.yaml` (`smart`, `code` presets)

### Changed
- `README` — positioning one-liner, version sync
- `check-key-hygiene` — `OPENAI_API_KEY` + tower audit hint
- `test.sh` — OpenAI validation + 3-connector registry
- `docs/CLEAN_WIRES.md` — audit command for tower checklist

## [3.10.0] — 2026-06-15 (Cycle 10 — connector registry + hermes-smart smoke)

### Added
- `config/connectors.yaml` — paste-key connector registry (groq, anthropic)
- `make connect-provider PROVIDER=<id>` — generic dispatch via `scripts/connect-provider.sh`
- `make smoke-hermes-smart` — prove `hermes-smart` / Anthropic route on kc-mini
- `docs/POSITIONING.md` — control-plane wedge vs LiteLLM / key wallets

### Changed
- `test.sh` — `connectors.yaml` registry validation (no secret-like values, script mapping)
- `README`, `docs/ENV.md`, `doctor` — connect-provider + smoke-hermes-smart hints

## [3.9.0] — 2026-06-15 (Cycle 9 — Anthropic connector + receiver bar)

### Added
- `make connect-anthropic` — paste `sk-ant-…` → `.env` → `push-env-mini` → mini restart
- `docs/ENV.md` — environment variable reference (gateway, providers, clients)
- Widget **receiver bar** — 3 LED rows (paths, API keys, network) + 5 theme presets (Classic R/G, Marantz, McIntosh, Denon, Pioneer)
- `tokens/scripts/homelab_status.py`, `receiver_themes.py` — connectivity probes for widget snapshot

### Changed
- `test.sh` — Anthropic validation, connector script checks, homelab_status smoke (18 LEDs, 5 presets)
- `tokens/config.json` — `receiver.default_preset: classic-rg`, webhook probes
- `README` — links `docs/ENV.md`, connect commands

## [3.8.0] — 2026-06-14 (Cycle 8 — Phase 2 Groq connector MVP)

### Added
- `docs/CONNECTOR_SPEC.md` — connector security model and Groq paste-key flow
- `modelrouter/env_store.py` — atomic `.env` writes + provider key validation
- `make connect-groq` — paste `gsk_…` → local `.env` → `push-env-mini` → mini restart

### Changed
- `test.sh` — `env_store` validation smoke
- `doctor` / `KEY_ROTATION.md` — `connect-groq` in ops hints
- `PRODUCT_VISION` / `config/product.yaml` — Phase 2 started

## [3.7.0] — 2026-06-12 (Cycle 7 — Phase 0/1 complete, calibration ops)

### Added
- `docs/CONTEXT_GUIDE.md` — preset selection by context window and cost
- `test.sh` — snapshot export guard (no raw API key prefixes in widget catalog JSON)
- `homelab-status` — 24h usage rollup header

### Changed
- `check_catalog.py` — every catalog model must have `context_window`
- `test.sh` — reconcile pidfile before optional health check
- `doctor` — `usage-rollup` and `homelab-status` in next steps
- `PRODUCT_VISION` — Phase 0 (clean wires) and Phase 1 (catalog/calibration) marked complete
- `CLEAN_WIRES` — calibration section points at rollup + context SSOT

## [3.6.1] — 2026-06-13 (tower wiring + daemon pidfile)

### Added
- `docs/TOWER_WIRING.md` — Tailscale gateway URL for kc-tower Linux clients

### Fixed
- `start-daemon.sh` — pidfile reconciled from port listener (`modelrouter_reconcile_pidfile`)
- Tower `client.env` uses mini Tailscale IP (mDNS fails on Linux)

### Changed
- `push-env-mini` includes `ANTHROPIC_API_KEY`; human backlog cleared in `HOMELAB_GOALS`
- `remote-health` / `smoke-tower` prefer `kc-tower` SSH and Tailscale gateway probe

## [3.6.0] — 2026-06-13 (Cycle 6 — clean wires + Console MVP)

### Added
- `make smoke-cursor`, `make smoke-tower` — verify Cursor and tower→mini gateway paths
- `docs/CURSOR_WIRING.md`, `docs/KEY_ROTATION.md`, `docs/CONSOLE_SPEC.md`
- `make check-key-hygiene`, `make usage-rollup` — salt/key checks and log metering
- Widget **Console** section — catalog presets + provider models grid (`console_grid.py`)
- `modelrouter/usage_rollup.py` — JSON log rollup by model/preset

### Changed
- `homelab-status` — tower SSH / client.env row
- `doctor` — `check-key-hygiene` in next steps
- `test.sh` — console grid smoke

## [3.5.0] — 2026-06-12 (iteration 4.5 — Cycle 4 capstone)

### Added
- `tokens/scripts/preset_catalog.py` — policy preset grid for widget snapshot
- `scripts/sync_preset_max_tokens.py`, `make sync-preset-tokens` — catalog → gateway `max_tokens`
- Widget **Policy presets** section (tier, max tokens, clients, project map)
- `docs/CYCLES.md` + repo-local `.cursor/commands/` — full `/cycle` pipeline
- `test.sh` — preset catalog smoke, sync check, CORE_APIS gitignore guard

### Changed
- Primary preset routes in `policy_presets.yaml` + gateway YAMLs carry catalog `max_tokens_default`
- `check_catalog.py` verifies primary `max_tokens` matches catalog
- `doctor` / `homelab-status` mention `make core-apis`

## [3.2.0] — 2026-06-12 (iteration 4.2)

### Added
- `make core-apis` — regenerates gitignored `data/CORE_APIS.md` (masked live API status)
- `modelrouter/core_api_list.py`, `scripts/update-core-api-list.sh`

### Changed
- `config/api_catalog.yaml` — gateway project keys, Anthropic pricing ref
- `docs/API_INVENTORY.md` — points to private core list

## [3.1.0] — 2026-06-12 (iteration 4.1 — Phase 1 start)

### Added
- `config/models_catalog.yaml` — preset/model catalog (cost tier, context, max tokens)
- `scripts/check_catalog.py`, `make check-catalog`, `modelrouter/models_catalog.py`
- `scripts/rotate-salt-key.sh`, `make rotate-salt-key` — salt only; master key unchanged

### Changed
- Master key policy documented: keep `crsr_*` gateway bearer for Cursor compatibility
- `PRODUCT_VISION.md` Phase 1 catalog items marked started

## [3.0.0] — 2026-06-12 (iteration cycle 3)

### Added
- `make push-client-env-tower` — tower gateway client env (no provider keys)
- Iteration docs 3.1–3.5; Cycle 2–3 committee checkpoint

### Fixed
- `stop.sh` frees port 3000 when pidfile is stale or orphaned
- `doctor.sh` — no JSON traceback when gateway down; preset check degrades gracefully

### Changed
- Phase 0 marked ~complete in `PRODUCT_VISION.md` (human wiring items flagged)
- `CLEAN_WIRES.md` / `HOMELAB_GOALS.md` — accurate human vs automated checklist
- README hardening note: laptop `127.0.0.1`, mini LAN `0.0.0.0` + mDNS

## [2.5.1] — 2026-06-12 (iteration 3.1)

### Fixed
- Daemon pidfile tracks `litellm` process (`start.sh` no longer pipes through `tee`)
- Health probes use loopback when gateway binds `0.0.0.0` (kc-mini LAN)
- `doctor` reconciles stale pidfile from port listener

### Changed
- Docs/scripts use `Kevins-Mac-mini.local` for LAN HTTP (`kc-mini-lan` SSH-only)
- `homelab-status` reads gateway URL from `config/hosts.yaml`
- `make push-client-env-tower` documented in README and doctor next-steps

## [2.5.0] — 2026-06-12 (iteration cycle 2)

### Added
- `scripts/check-master-key.sh` — fail-closed startup on placeholder keys
- `scripts/check_presets.py` + `make check-presets` — preset SSOT drift check
- `scripts/consolidate-keys.sh` + `make consolidate-keys`
- Widget session token (`X-Widget-Token`) on mutating routes
- Iteration docs 2.1–2.5, committee review doc

### Fixed
- `rotate-master-key` refreshes `MODELROUTER_KEY_*` via `--refresh`
- `route_policy` — `--all` no longer overwritten by single-project recommend
- `fetch_equity` — live fetch when `force_live` (skip paper status.json)
- `equity_remote_runner` — equity total includes more than 6 assets
- `api_assess` — preset context from YAML list; offline summary IndexError
- MCP `list_models` — error JSON when gateway down
- Wallet snapshot redacts full on-chain addresses
- `client.env.example` — dotenv-safe tower template

### Changed
- `deploy-to-mini.sh` runs `remote-health` after install
- launchd plist `ThrottleInterval` 30s

## [1.5.0] — 2026-06-12 (iteration cycle 1)

### Added
- Homelab iteration framework (`docs/iterations/`, `VERSION`)
- Policy presets: `hermes-fast`, `hermes-smart`, `cheap`, `code`, `review`, `offline`
- `config/hosts.yaml`, `config/projects.yaml`, `make homelab-status`
- `make doctor`, `make cost-review`, `make test`, `make lint`
- Route policy + MCP server + keys widget integration
- MIT LICENSE, GitHub smoke CI

### Fixed
- Healthcheck loads `.env`; daemon waits for health
- Deploy excludes `.git`; broken mini venv auto-repair
- Docker compose passes Groq/Mistral/Gemini env vars

### Stubbed
- OpenRouter (`config/openrouter.stub.yaml`)

## [1.0.0] — initial

- LiteLLM gateway, deploy-mini, tokens widget ingest

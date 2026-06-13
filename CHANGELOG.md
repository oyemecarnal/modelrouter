# Changelog

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

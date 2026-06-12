# Changelog

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

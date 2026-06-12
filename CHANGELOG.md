# Changelog

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

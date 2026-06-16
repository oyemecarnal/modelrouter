# Connector spec (Phase 2)

**Status:** Four paste-key connectors (Groq, Anthropic, OpenAI, Mistral) + `config/connectors.yaml` registry. OAuth deferred.  
**SSOT for signup links:** `config/api_catalog.yaml` (registry mirrors in `config/connectors.yaml`)  
**Vault write:** `modelrouter/env_store.py` → local `.env` only; never repo or chat.

## Goal

Paste API key → validated → stored in gateway `.env` on kc-mini → gateway restarted. Keys never touch git, logs, or widget snapshots.

## Security model (non-negotiable)

| Rule | Enforcement |
|------|-------------|
| Keys never committed | `.gitignore` on `.env`; `test.sh` snapshot guard |
| Keys never printed | Scripts mask output; `push-env-to-mini.sh` uses temp file over SSH |
| Keys never in widget JSON | `preset_catalog` / `console_grid` are catalog-only |
| Atomic writes | `env_store.update_env_file` writes via temp + rename |
| Validate before store | `env_store.validate_provider_key` per env var prefix |
| Staged consent | Paste-key only in Phase 2; OAuth needs separate spec |
| Tower agents | Provider keys on kc-mini only — `make audit-tower-wires` |

## Connector registry

`config/connectors.yaml` lists paste-key connectors. Generic entry:

```bash
make connect-provider PROVIDER=anthropic
./scripts/connect-provider.sh   # lists ids
```

Receiver widget API KEY row reads the same registry (`tokens/scripts/homelab_status.py`).

## Commands

```bash
make connect-groq        # paste → local .env → push-env-mini
make connect-anthropic   # paste sk-ant-… → mini (hermes-smart / review)
make connect-openai      # paste sk-… → mini (smart / code)
make connect-mistral     # paste Mistral key → mini
make connect-google      # paste Google AI key → mini
make connect-deepseek    # paste DeepSeek key → mini
make connect-together    # paste Together key → mini
make connect-provider PROVIDER=<id>
make audit-tower-wires   # stray provider keys on kc-tower
make clean-tower-wires   # push client.env + re-audit
make check-key-hygiene   # verify keys on laptop + mini
make push-env-mini       # manual key sync when needed
```

Docs: `docs/ENV.md`

## Verify

```bash
make check-key-hygiene
make doctor
make smoke-tower         # hermes-fast / cheap via gateway
make smoke-hermes-smart  # Anthropic route on mini
```

## Future (Phase 2.5+)

- OAuth / refresh tokens
- Widget “Add provider” button (signup links shown for missing keys in Cycle 13)
- 1Password write from connector (read-only via `load_secrets.py` today)
- OpenRouter wiring (stub stays)
- Google/Gemini paste-key connectors

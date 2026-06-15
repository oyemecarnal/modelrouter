# Connector spec (Phase 2 MVP)

**Status:** Groq paste-key flow first (`make connect-groq`). OAuth deferred.  
**SSOT for signup links:** `config/api_catalog.yaml`  
**Vault write:** `modelrouter/env_store.py` → local `.env` only; never repo or chat.

## Goal

One provider end-to-end: user pastes API key → validated → stored in gateway `.env` on kc-mini → gateway restarted. Keys never touch git, logs, or widget snapshots.

## Security model (non-negotiable)

| Rule | Enforcement |
|------|-------------|
| Keys never committed | `.gitignore` on `.env`; `test.sh` snapshot guard |
| Keys never printed | Scripts mask output; `push-env-to-mini.sh` uses temp file over SSH |
| Keys never in widget JSON | `preset_catalog` / `console_grid` are catalog-only |
| Atomic writes | `env_store.update_env_file` writes via temp + rename |
| Validate before store | `env_store.validate_provider_key` per env var prefix |
| Staged consent | Paste-key only in Phase 2; OAuth needs separate spec |

## Phase 2 MVP flow (Groq)

```
User → make connect-groq
         ├─ paste gsk_… (hidden prompt)
         ├─ validate prefix
         ├─ update laptop .env (atomic)
         ├─ make push-env-mini GROQ_API_KEY
         └─ optional: restart mini gateway
```

Signup: [console.groq.com/keys](https://console.groq.com/keys) (GitHub OAuth for console; API key is separate).

## Connector registry (Phase 2.5)

`config/connectors.yaml` lists paste-key connectors. Generic entry:

```bash
make connect-provider PROVIDER=anthropic
make connect-provider PROVIDER=groq
./scripts/connect-provider.sh   # lists ids
```

## Future (Phase 2.5+)

- OAuth / refresh tokens
- Widget "Add provider" button
- 1Password write from connector (read-only via `load_secrets.py` today)
- OpenRouter wiring (stub stays)

## Commands

```bash
make connect-groq        # paste → local .env → push-env-mini
make connect-anthropic   # paste sk-ant-… → mini (hermes-smart / review)
make check-key-hygiene # verify keys on laptop + mini
make push-env-mini     # manual key sync when needed
```

Docs: `docs/ENV.md`

## Verify

```bash
make check-key-hygiene
make doctor            # GROQ_API_KEY set on mini
make smoke-tower       # hermes-fast uses Groq via gateway
```

## Future (Phase 2.5+)

- ~~`make connect-anthropic`~~ — done (Cycle 9)
- Connector row in Console widget (status only, no key display) — receiver bar LEDs
- `config/connectors.yaml` registry driving a generic `connect-provider.sh`

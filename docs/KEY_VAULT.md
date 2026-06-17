# Key vault — network API key scraper

Centralizes API keys from your homelab into one vault, with **permissions**, **opt-out**, **multiple keys per service**, and **routing-aware selection**.

## Quick start

```bash
make vault-scrape              # discover keys on laptop + mini (masked)
make vault-scrape-collect      # ingest values → data/key_vault.json (policy-gated)
make vault-list                # masked inventory + source host/path
make vault-export-dry          # preview .env merge
make vault-export              # write primary + __ALT_N keys to .env
make check-alt-keys            # verify __ALT_N vars vs LiteLLM config (warn-only)
make check-alt-keys-mini       # same audit on kc-mini .env
make push-alt-keys-mini        # sync alt keys laptop → kc-mini .env
make vault-sync-alts           # export + push alts (see multi-key hint)
make vault-sync-alts-restart   # same + restart kc-mini gateway
make vault-rotate-drill        # dry-run 429 rotate pipeline readiness
make connect-alt-key PROVIDER=groq  # paste GROQ_API_KEY__ALT_1
make bootstrap-mini            # deploy + daemon-enable + push alts
```

## Architecture

```
┌─────────────┐   SSH / local    ┌──────────────────┐
│ laptop      │ ───────────────► │ data/key_vault   │
│ kc-mini     │   allowed paths  │ .json (gitignored)│
│ kc-tower    │   + permissions  └────────┬─────────┘
└─────────────┘                           │
                                          ▼ export / select
                                 ┌──────────────────┐
                                 │ modelrouter/.env │
                                 │ GROQ_API_KEY     │
                                 │ GROQ_API_KEY__ALT_1 │
                                 └──────────────────┘
```

Built on `modelrouter/machine_inventory.py` (allowed paths only — see `config/inventory.yaml`).

## Permissions (`config/key_vault.yaml`)

| Control | Purpose |
|---------|---------|
| `permissions.collect_values` | Master switch for `--collect` |
| `permissions.deny_vars` | Never ingest (mnemonics, exchange secrets) |
| `permissions.deny_collect_hosts` | Block value pull from a host |
| `permissions.require_opt_in` | Vars need `opt_in.VAR_NAME: true` |
| `export_deny_vars` / `export_deny_prefixes` | Block vault → `.env` export (e.g. `MODELROUTER_KEY_*`) |
| `hosts.*.collect` | Per-host collection (tower default: false) |

Tower keys are **discovered** but not pulled unless you explicitly enable `collect: true`.

## Multi-key per service

Each service in `config/key_vault.yaml` → `services:` defines:

- `env_var` — canonical name
- `max_keys` — cap alternates (extras marked `enabled: false`)
- `strategy` — `prefer_primary` or `round_robin`
- `tags` — `fast`, `cheap`, `smart`, etc.

Export writes:

- `GROQ_API_KEY` — highest-priority enabled key
- `GROQ_API_KEY__ALT_1`, `__ALT_2` — additional keys for manual rotation or future gateway cycling

Disable a key without deleting:

```bash
python -m modelrouter.key_vault disable <entry_id>
```

## Routing integration

`routing:` maps presets to preferred env vars:

```bash
python -m modelrouter.key_vault select GROQ_API_KEY --preset hermes-fast
```

`route_policy.py` reads widget quota pressure; vault `select` picks **which physical key** when multiple exist.

On gateway **429**, `logging_callback` calls `record_rate_limit()` — advances round-robin in the vault and appends to `data/key_rotate_hints.json`. Apply the hint:

```bash
make vault-rotate-export-dry   # preview
make vault-rotate-export       # merge next primary into .env
make vault-rotate-push         # export + push rotated keys to kc-mini
```

**Opt-in auto-export on 429:** set `MODELROUTER_AUTO_VAULT_ROTATE=1` on the gateway host — `logging_callback` will call `apply_last_rotate_export` after a successful rotate hint (does not push to mini).

**Opt-in gateway restart:** set `MODELROUTER_AUTO_VAULT_RESTART=1` with auto-rotate — runs `make restart` after a successful export so LiteLLM picks up new keys.

**Opt-in push to mini:** set `MODELROUTER_AUTO_VAULT_PUSH=1` on the gateway host (with auto-rotate) — runs `make vault-rotate-push` after export+restart. Clears the widget ROTATE LED when push succeeds.

**LiteLLM alt routes:** policy presets include `__ALT_1` deployments for Groq, OpenAI, Mistral, and Anthropic when exported from vault (`simple-shuffle` load-balances). You need **two or more enabled keys per provider** in the vault for `__ALT_1` to populate — scrape additional keys with `make vault-scrape-collect`, or set `GROQ_API_KEY__ALT_1=...` in `.env` and re-scrape. Then `make vault-sync-alts` exports and pushes alts to mini.

## Tangem / cold wallets

Not part of the key vault (watch-only addresses). Set `TANGEM_BTC_ADDRESS`, `TANGEM_ETH_ADDRESS`, `TANGEM_SOL_ADDRESS` in `.env` — wallet presets pick them up automatically.

## Security

- Never commit `data/key_vault.json`
- CLI never prints raw secrets (fingerprints only)
- Same allowed-path rules as `make inventory`
- Provider validation via `env_store.validate_provider_key` where patterns exist

## Related

- `make inventory` / `make inventory-mini` — masked audit only
- `make keys-sync` — legacy fill-empty from known `.env` files
- `make consolidate-keys` — human checklist toward mini-canonical store
- `docs/INVENTORY.md`, `docs/CONNECTOR_SPEC.md`

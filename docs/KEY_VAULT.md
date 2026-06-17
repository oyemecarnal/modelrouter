# Key vault — network API key scraper

Centralizes API keys from your homelab into one vault, with **permissions**, **opt-out**, **multiple keys per service**, and **routing-aware selection**.

## Quick start

```bash
make vault-scrape              # discover keys on laptop + mini (masked)
make vault-scrape-collect      # ingest values → data/key_vault.json (policy-gated)
make vault-list                # masked inventory + source host/path
make vault-export-dry          # preview .env merge
make vault-export              # write primary + __ALT_N keys to .env
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

`route_policy.py` reads widget quota pressure today; vault `select` adds **which physical key** to use when multiple exist. Gateway cycling (auto-swap on 429) is a follow-up — alternates are exported now.

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

# Machine inventory scraper

Read-only audit of **allowed folders** for API keys, tokens, and crypto **surfaces** (where wallets live — not the keys themselves).

```bash
make inventory          # this machine, masked table
make inventory-mini     # same on kc-mini via SSH
```

Output JSON: `data/inventory_snapshot.json` (gitignored via `data/`).

## Is this like a crypto wallet?

**Similar goal, different job.**

| Crypto wallet | ModelRouter inventory |
|---------------|------------------------|
| Holds keys securely | **Does not hold** keys |
| Signs transactions | **Read-only** scan |
| Encrypted vault | Masked report + locations |
| You trust it with secrets | You trust it to **find** secrets already on disk |

Think of it as a **wallet-style inventory harness**: “what credentials exist on this machine, and where?” — so you can consolidate into ModelRouter’s vault (kc-mini) and **untangle wires** (`docs/CLEAN_WIRES.md`).

We do **not**:
- Read private keys, mnemonics, or MetaMask vault bytes
- Store or move funds
- Replace 1Password / hardware wallets

We **do**:
- List env vars like `GROQ_API_KEY` with masked values
- Detect `~/.ethereum/keystore/UTC--*` and show **public address** only
- Report MetaMask / Ledger Live **presence** (app data exists)
- Flag `PRIVATE_KEY` / `MNEMONIC` in `.env` with ⚠ wallet warning

## Allowed paths only

Configured in `config/inventory.yaml`:

- `~/dev`, `~/dev/modelrouter`, `~/.config`, selected `~/Library/Application Support`
- Explicit: `~/.zshrc`, shell profiles
- Skips: `node_modules`, `.venv`, `.git`, large files

Edit `allowed_roots` to add paths — never scan whole `$HOME` by default.

## Crypto surfaces

| Surface | What we report |
|---------|----------------|
| Ethereum keystore UTC JSON | Public `address` (masked) |
| Solana `id.json` | “present — not read” |
| Coinbase CDP `cdp_api_key.json` | Key id (masked) |
| MetaMask / Ledger Live | Directory exists |
| Wallet env vars | Masked value + warning |

## Security

- Run locally or on mini over SSH; output is masked
- Do not commit `data/inventory_snapshot.json`
- Rotate any key that appeared in unexpected paths
- Goal: **one canonical store** on kc-mini `modelrouter/.env` + 1Password

## Product path

Phase 2 **Connector harness** (`docs/PRODUCT_VISION.md`) builds on this: login at provider → vault write, instead of scattered `.env` files.

**Network key vault** (`docs/KEY_VAULT.md`): `make vault-scrape-collect` ingests allowed hosts into `data/key_vault.json`, then `make vault-export` merges primary + alternate keys into `.env` with opt-out permissions.

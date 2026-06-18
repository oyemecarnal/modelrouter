# Security

ModelRouter handles LLM provider API keys and project virtual keys. Treat this repo and your deployment as sensitive infrastructure.

## Never commit

- `.env`, `secrets.yaml`, `tokens/.env.local`, `tokens/config.local.json`
- `config/hosts.local.yaml` (operator-specific hostnames and IPs)
- `config/modelrouter.local.yaml`, `data/`, `.pids/`
- Generated inventories with live key values (`data/key_vault.json`, `data/CORE_APIS.md`)

These paths are listed in `.gitignore`. If you accidentally commit secrets, rotate them immediately and purge from git history.

## Recommended setup

1. Copy examples: `.env.example` → `.env`, `secrets.example.yaml` → `secrets.yaml`
2. Use [1Password CLI](https://developer.1password.com/docs/cli/) (`op://` refs in `secrets.yaml`) where possible
3. Keep provider keys on the **gateway host** only; remote agents use `MODELROUTER_KEY_*` virtual keys via `config/client.env.example`
4. Copy `config/hosts.local.yaml.example` → `config/hosts.local.yaml` for homelab hostnames (never commit the local file)

## Reporting issues

If you discover a vulnerability in ModelRouter itself, open a private security advisory on GitHub or contact the repository owner directly. Do not open public issues for undisclosed key leaks or exploit details.

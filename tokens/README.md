# ModelRouter Keys

Square desktop panel for AI API usage and local key inventory. Lives under `modelrouter/tokens/` and scans `~/dev` plus `modelrouter/.env`.

## Quick start

```bash
cd ~/dev/modelrouter
make keys-widget-install   # venv + launchd refresh job
make keys-widget           # open the panel
```

Or from this directory:

```bash
./scripts/install.sh
.venv/bin/python3 widget/desktop_widget.py
```

## UI

- **Square window** (~420×420) with usage bars and per-key cards (masked values)
- **Refresh** — re-runs `fetch_usage.py` and reloads the snapshot
- **Edit** — opens `tokens/.env.local` in TextEdit (created from `.env.local.example` if missing)

## Secrets

```bash
cp .env.local.example .env.local
# add keys not already in modelrouter/.env or other ~/dev projects
```

The fetcher also reads `modelrouter/.env`, `secrets.yaml` (1Password refs), and `~/.zshrc`.

## Providers

| Provider | Live quota | Source |
|----------|------------|--------|
| OpenAI Codex | Yes | `~/.codex/auth.json` |
| Cursor | Yes | Chrome cookies |
| Claude | Yes | Chrome cookies |
| Gemini | Partial | API key or Gemini CLI OAuth |
| OpenRouter | Yes | credits API |
| GitHub Copilot | Yes | `gh auth login -s copilot` |
| Groq / Mistral | Key status | `modelrouter/.env` |

## Config

`config.json` — toggle providers, window size, refresh interval:

- `app_name`: window title
- `widget_size`: square dimensions (default 420)
- `modelrouter_root`: path to modelrouter repo for `.env` scan
- `show_configured_keys`: per-key inventory cards

## Files

| Path | Purpose |
|------|---------|
| `scripts/fetch_usage.py` | Usage + key snapshot |
| `scripts/key_inventory.py` | Scan ~/dev for API keys |
| `widget/desktop_widget.py` | Native pywebview panel |
| `widget/index.html` | UI |
| `.env.local` | Local overrides (gitignored) |

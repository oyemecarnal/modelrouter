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

- **Square window** (~500×500) with usage bars and per-key cards (masked values)
- **Receiver bar** — stereo-style connectivity LEDs (paths, API keys, network/webhooks)
- **Theme presets** — Classic R/G (default), Marantz, McIntosh, Denon, Pioneer, Tube Amp, Tek Scope, Luxman, Nakamichi, Fuse Panel, Vintage Radio; choice persists in browser storage. Header **Theme** dropdown (discreet). See `docs/THEME_DESIGN.md`.
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
- `equity`: live broker balances via coinbot (see below)

### Live equity (`equity`)

Unified **portfolio** across exchanges (coinbot), Kalshi, and watch-only cold wallets (Tangem):

```json
"equity": {
  "brokers": ["kraken", "coinbase", "kalshi"],
  "include_wallets": true,
  "broker_routes": {
    "kraken": { "remote": false, "host": "local", "coinbot_root": "~/dev/coinbot" },
    "coinbase": { "remote": true, "host": "kc-mini-lan" },
    "kalshi": { "provider": "kalshi" }
  }
},
"wallets": {
  "include_in_equity": true,
  "presets": [{ "label": "Tangem BTC", "chain": "bitcoin", "address": "bc1…", "kind": "cold" }]
}
```

Set `TANGEM_BTC_ADDRESS` / `TANGEM_ETH_ADDRESS` / `TANGEM_SOL_ADDRESS` in `modelrouter/.env` (or `tokens/.env.local`) — watch-only public addresses, no keys. ETH balance uses public RPC when `ETHERSCAN_API_KEY` is unset; Etherscan still needed for transaction history. Cold wallets refresh on a slower cache (`cold_cache_seconds`).

Kalshi reads `POLYMARKET_KALSHI_*` from `~/dev/Kalshi_bot/.env`. Kraken on laptop coinbot uses plaintext or encrypted keys (`~/.coinbot/master_{instance_id}.key` on the fetch host).

## Files

| Path | Purpose |
|------|---------|
| `scripts/fetch_usage.py` | Usage + key snapshot |
| `scripts/fetch_equity.py` | Live broker equity (coinbot SSH) |
| `scripts/equity_remote_runner.py` | Remote coinbot balance runner |
| `scripts/homelab_status.py` | Receiver LED probes |
| `scripts/receiver_themes.py` | Five preset palettes (+ custom via config) |

### Receiver themes

Edit `tokens/config.json` → `receiver.default_preset` (`classic-rg`, `marantz`, `mcintosh`, `denon`, `pioneer`).

Override any color infinitely:

```json
"receiver": {
  "default_preset": "classic-rg",
  "background": "#1a0505",
  "led": { "ok": "#00ff55", "off": "#4a1010" }
}
```

Add network probes under `receiver.webhooks` (reachability only, no secrets). Paste-key connectors from `config/connectors.yaml` drive the API KEYS row; missing keys show signup links in the widget.

**＋ Provider** menu opens a paste modal (`POST /connectors/paste`) — validates, writes modelrouter `.env`, pushes to kc-mini. Terminal fallback: `make connect-<provider>`.

| `scripts/key_inventory.py` | Scan ~/dev for API keys |
| `widget/desktop_widget.py` | Native pywebview panel |
| `widget/index.html` | UI |
| `.env.local` | Local overrides (gitignored) |

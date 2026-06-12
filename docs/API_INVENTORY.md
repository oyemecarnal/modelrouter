# API Key Inventory

Generated from machine audit. **Values are never stored in this doc.**

Run `./scripts/discover-keys.sh` to refresh.

## LLM / AI (ModelRouter)

| Key | MacBook | kc-mini | Source project | ModelRouter status |
|-----|---------|---------|----------------|-------------------|
| `OPENAI_API_KEY` | ✅ `.zshrc`, `smalshi/Codex` | ✅ `coinbot`, `smalshi`, `modelrouter` | smalshi, coinbot | **Fill** — empty in modelrouter `.env` |
| `ANTHROPIC_API_KEY` | ❌ | ✅ `modelrouter` | — | **Get from mini** or [console.anthropic.com](https://console.anthropic.com) |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | ❌ | ✅ `smalshi` | smalshi | **Fill from mini** — same key for Gemini |
| `OPENROUTER_API_KEY` | ❌ | ✅ `smalshi` | smalshi | Optional fallback provider |
| `CURSOR_API_KEY` | ✅ `smalshi/Codex` | ✅ `smalshi` | smalshi | Cursor cloud agents — **not** LiteLLM routing |
| `MODELROUTER_MASTER_KEY` | ✅ placeholder | ✅ | modelrouter | Change from `sk-modelrouter-change-me` |
| `LITELLM_SALT_KEY` | ✅ placeholder | ✅ | modelrouter | Change for production DB |

### 1Password refs (configured, CLI not installed on MacBook)

| Key | Reference |
|-----|-----------|
| `OPENAI_API_KEY` | `op://Personal/OpenAI/credential` |
| `ANTHROPIC_API_KEY` | `op://Personal/Anthropic/credential` |
| `GOOGLE_API_KEY` | `op://Personal/Google AI/credential` |

Install: `brew install 1password-cli && op signin`

## Market / trading (not LLM — keep separate)

| Key | MacBook | kc-mini | Project |
|-----|---------|---------|---------|
| `POLYGON_API_KEY` | ❌ (commented in project_kc) | ✅ `coinbot` | coinbot — market data |
| `KRAKEN_API_KEY` / `KRAKEN_API_SECRET` | ✅ `coinbot` | ✅ encrypted `coinbot` | coinbot |
| `POLYMARKET_*` / `POLYMARKET_KALSHI_*` | ✅ partial `Kalshi_bot` | ✅ full `Kalshi_bot` | Kalshi_bot |
| `COINBASE_CDP_KEY_FILE` | — | ✅ `coinbot` | coinbot |

## Messaging / automation

| Key | MacBook | kc-mini | Project |
|-----|---------|---------|---------|
| `TELEGRAM_BOT_TOKEN` | ✅ `coinbot` | ✅ `coinbot`, `openclaw` | coinbot, openclaw |
| `KC_TELEGRAM_BOT_TOKEN` | ✅ `project_kc/signals` | — | project_kc |

## Suggested keys you don't have yet

High value for ModelRouter / agent workflows:

| Provider | Why | Get key |
|----------|-----|---------|
| **Groq** | Very fast inference, generous free tier | [console.groq.com](https://console.groq.com) |
| **Together AI** | Open-weight models, cheap | [api.together.xyz](https://api.together.xyz) |
| **Mistral** | Direct Claude competitor, EU hosting | [console.mistral.ai](https://console.mistral.ai) |
| **DeepSeek** | Cheap strong reasoning | [platform.deepseek.com](https://platform.deepseek.com) |
| **Cohere** | Embeddings + Command models | [dashboard.cohere.com](https://dashboard.cohere.com) |
| **Fireworks AI** | Fast open models | [fireworks.ai](https://fireworks.ai) |
| **xAI (Grok)** | Alternative frontier model | [x.ai/api](https://x.ai/api) |
| **Perplexity** | Search-grounded answers | [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api) |
| **Tavily / Serper / Brave** | Web search tools for agents | tavily.com, serper.dev, brave.com/search/api |
| **Hugging Face** | Inference API for open models | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |

Lower priority unless you need them:

- **Replicate** — image/audio models
- **ElevenLabs** — voice (you have voice AI agent in agency-agents)
- **AssemblyAI** — transcription
- **AWS Bedrock** — if you want enterprise multi-model via AWS

## Security notes

1. **`OPENAI_API_KEY` is in `~/.zshrc` in plaintext** — move to 1Password + `secrets.yaml`, remove from shell profile.
2. **Never commit `.env`** — already gitignored.
3. **Rotate** any key that may have been exposed in chat logs or shell history.
4. **kc-mini is your secrets hub** — most keys are already there; use `make deploy-mini` + `sync-keys --from-mini`.

## Quick fill ModelRouter

```bash
./scripts/discover-keys.sh          # audit (masked)
./scripts/sync-keys.sh --dry-run    # preview
./scripts/sync-keys.sh              # fill from MacBook projects
./scripts/sync-keys.sh --from-mini  # also pull kc-mini modelrouter .env
make restart
```

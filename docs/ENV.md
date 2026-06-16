# Environment variables — ModelRouter

**Canonical store:** `modelrouter/.env` on **kc-mini** (production gateway).  
**Laptop:** `~/dev/modelrouter/.env` for dev + `make push-env-mini` sync.  
**Never commit** `.env` — see `.env.example` for the template.

## Quick connect (provider keys)


| Provider  | Command                  | Env var             | Key shape  |
| --------- | ------------------------ | ------------------- | ---------- |
| Groq      | `make connect-groq`      | `GROQ_API_KEY`      | `gsk_…`    |
| Anthropic | `make connect-anthropic` | `ANTHROPIC_API_KEY` | `sk-ant-…` |
| OpenAI    | `make connect-openai`    | `OPENAI_API_KEY`    | `sk-…`     |
| Mistral   | `make connect-mistral`   | `MISTRAL_API_KEY`   | alphanumeric |
| Google    | `make connect-google`    | `GOOGLE_API_KEY`    | `AIza…`      |
| DeepSeek  | `make connect-deepseek`  | `DEEPSEEK_API_KEY`  | `sk-…`       |
| Together  | `make connect-together`  | `TOGETHER_API_KEY`  | alphanumeric |


Generic registry: `make connect-provider PROVIDER=<id>` (see `config/connectors.yaml`).

Both scripts: validate → save local `.env` → `push-env-mini` → restart mini gateway.

Signup: [Anthropic console keys](https://console.anthropic.com/settings/keys)

## Namespace rules


| Prefix                                   | Where                   | Purpose                                  |
| ---------------------------------------- | ----------------------- | ---------------------------------------- |
| `MODELROUTER_`*                          | Gateway `.env`          | Master key, port, host                   |
| `MODELROUTER_KEY_*`                      | Client `client.env`     | Per-project virtual keys                 |
| `*_API_KEY` (OpenAI, Groq, Anthropic, …) | **kc-mini `.env` only** | Provider secrets                         |
| `CURSOR_API_KEY`                         | Laptop / widget         | Cursor product API — **not** gateway key |


See `docs/CLEAN_WIRES.md` for the full separation manifesto.

## Gateway (required)

```bash
MODELROUTER_HOST=127.0.0.1      # laptop dev; mini often 0.0.0.0
MODELROUTER_PORT=3000
MODELROUTER_MASTER_KEY=         # Cursor uses this as API key (crsr_* OK)
LITELLM_SALT_KEY=               # Must differ from master key
```

## Provider keys (kc-mini)

Used by LiteLLM routing in `config/modelrouter*.yaml`:


| Variable                            | Presets / routes                  |
| ----------------------------------- | --------------------------------- |
| `GROQ_API_KEY`                      | `cheap`, `hermes-fast`, fallbacks |
| `ANTHROPIC_API_KEY`                 | `hermes-smart`, `review`          |
| `OPENAI_API_KEY`                    | `code`, `smart`, embeddings       |
| `MISTRAL_API_KEY`                   | `code`, fallbacks                 |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Gemini routes                     |
| `OPENROUTER_API_KEY`                | Stubbed — optional backup only    |


## Client env (tower / agents)

Template: `config/client.env.example`  
Deploy: `make push-client-env-tower`

Tower gets **gateway URL + project keys only** — no provider `*_API_KEY`.

## Widget / tokens


| File                        | Purpose                                |
| --------------------------- | -------------------------------------- |
| `tokens/.env.local`         | Extra keys for widget quota fetch only |
| `tokens/.env.local.example` | Template                               |


Widget keys are **not** the gateway vault — keep providers on mini.

## 1Password (optional)

`secrets.yaml` + `scripts/load_secrets.py` — `op://` references override empty `.env` vars at gateway start.

## Ops commands

```bash
make connect-anthropic     # paste sk-ant-… → mini
make connect-groq          # paste gsk_… → mini
make push-env-mini         # sync selected vars to mini
make keys-sync-mini        # pull mini .env → laptop
make check-key-hygiene     # laptop + mini key audit
make doctor                # masked provider key status
```

## Verify Anthropic

```bash
make check-key-hygiene
make doctor                # ANTHROPIC_API_KEY set on mini
make smoke-hermes-smart    # hermes-smart chat via mini gateway
```


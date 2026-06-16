# Why ModelRouter? (plain English)

You asked: **what is this doing for me that I can't already do?**

Short answer: **you can do everything without ModelRouter** — but keys, models, and logs end up scattered. ModelRouter is the **one front door** on your Mac mini so Cursor, Hermes, and bots share the same rules.

---

## Without ModelRouter (what you already know how to do)

| You do this | Result |
|-------------|--------|
| Put `OPENAI_API_KEY` in each app's `.env` | Each app calls OpenAI/Groq/Anthropic **directly** |
| Pick `gpt-4o` or `claude-…` in each app | Every app has its own model names and SDKs |
| Rotate a key | Hunt laptop, tower, coinbot, `.zshrc` |
| "How much did Hermes spend?" | Check 3 dashboards or guess |

**That works.** Most solo devs never use a gateway.

---

## With ModelRouter (what changes)

```
Cursor / Hermes / coinbot
        │
        │  one URL: http://<mini>:3000/v1
        │  one client key (MODELROUTER_MASTER_KEY or project key)
        ▼
   ModelRouter on kc-mini  ← real provider keys live HERE only
        │
        ▼
   OpenAI · Groq · Anthropic · Gemini · Ollama …
```

| Benefit | What it means for you |
|---------|------------------------|
| **One vault** | Vendor keys on kc-mini `.env` only — not copied to tower |
| **Presets** | Apps ask for `hermes-fast` or `cheap`, not vendor model IDs |
| **Fallbacks** | Groq down → try Mistral → local — configured once |
| **One meter** | `make usage-rollup` sees **gateway** traffic in one log |
| **Ops UI** | Widget receiver bar: mini up? keys set? tower→mini OK? |
| **Paste-key flows** | `make connect-groq` → validate → push to mini → restart |

Under the hood it's **LiteLLM** plus homelab scripts, connectors, and docs — not magic AI.

---

## What ModelRouter is NOT

- Not a replacement for **Coinbase/Kraken API keys** (coinbot still needs exchange keys in its own `.env`)
- Not Cursor's product API (`CURSOR_API_KEY` is separate)
- Not required if you only use one app and one provider and don't care about central logs

---

## The coinbot / tower issue (why it keeps coming up)

`make audit-tower-wires` flags **`OPENAI_API_KEY` in `~/dev/coinbot/.env` on the tower**.

That usually means coinbot might call **OpenAI directly** instead of through the mini gateway — so:

- Gateway logs **won't** show coinbot LLM usage
- You rotate keys in **two places**
- It breaks the "clean wires" rule in `docs/CLEAN_WIRES.md`

**Coinbase/CDP keys in coinbot `.env` are fine** — the audit only looks for LLM provider keys (`OPENAI_*`, `GROQ_*`, etc.).

### Your choices

| Choice | Action |
|--------|--------|
| **Use gateway for coinbot LLM** | Remove `OPENAI_API_KEY` from tower coinbot `.env`; `source ~/.config/modelrouter/client.env` |
| **Keep coinbot direct** | Document exception in `config/wire_exceptions.yaml` and accept split metering |
| **Key is unused cruft** | Delete it; test coinbot still runs |

```bash
make guide-tower-strays    # shows strays + steps
make clean-tower-wires    # refresh tower client.env + re-audit
```

---

## When ModelRouter is worth it for you

**Worth it if:**

- Cursor on laptop **and** agents on tower **and** you want one key store on mini
- You want preset names (`hermes-smart`) and fallbacks without editing every bot
- You want the widget / `homelab-status` picture of what's connected

**Skip the guilt if:**

- Only Cursor + manual keys on mini is enough
- coinbot LLM direct is intentional (document the exception)

---

## Commands mapped to "why"

| Command | Why you'd run it |
|---------|------------------|
| `make homelab-status` | "Is everything wired?" |
| `make connect-<provider>` | "Put this key on mini safely" |
| `make smoke-cursor` | "Does Cursor hit my gateway?" |
| `make smoke-tower` | "Does tower hit mini?" |
| `make usage-rollup` | "Who used which preset lately?" |
| `make daemon-enable` | "Keep laptop gateway up for Cursor" (`docs/LAPTOP_DAEMON.md`) |
| `make package-personal` | "Tarball to share/sell self-host bundle" |

---

## Read next

- `docs/CLEAN_WIRES.md` — rules (keys on mini, clients use gateway)
- `docs/CURSOR_WIRING.md` — Cursor settings
- `docs/TOWER_WIRING.md` — tower `client.env`
- `docs/ENV.md` — variables and connectors
- `docs/POSITIONING.md` — product wedge vs LiteLLM / Portkey

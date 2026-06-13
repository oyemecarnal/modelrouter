# Key rotation checklist

## Groq (manual — prior exposure)

1. Revoke old key at [console.groq.com](https://console.groq.com)
2. Create new key; update `GROQ_API_KEY` in laptop `modelrouter/.env`
3. `make push-env-mini`
4. `make restart` on mini if needed: `ssh kc-mini-lan 'cd ~/dev/modelrouter && make restart'`

## Anthropic (hermes-smart / review)

1. Add `ANTHROPIC_API_KEY` to laptop `.env` (or mini directly)
2. `make push-env-mini`
3. `make doctor` — Anthropic should show set on mini

## Salt (automated — does not change Cursor master key)

```bash
make rotate-salt-key
make push-env-mini
```

## Master key (only if intentionally rewiring Cursor)

```bash
make rotate-master-key   # also rotates salt in that script
# Update Cursor API key + tower client.env + make push-client-env-tower
```

## Verify

```bash
make check-key-hygiene
```

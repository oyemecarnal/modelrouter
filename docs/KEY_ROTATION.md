# Key rotation checklist

## Groq (optional)

Rotation waived for homelab. Rotate only if you revoke the key at [console.groq.com](https://console.groq.com), then `make push-env-mini`.

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

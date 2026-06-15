# Key rotation checklist

## Groq (connector MVP)

```bash
make connect-groq    # paste gsk_… → local .env → push-env-mini → restart mini
```

Rotation waived unless you revoke at [console.groq.com](https://console.groq.com). See `docs/CONNECTOR_SPEC.md`.

Legacy local-only setup (optional GitHub secret): `make groq-setup`

## Anthropic (hermes-smart / review)

```bash
make connect-anthropic   # paste sk-ant-… → local .env → push-env-mini → restart mini
```

Docs: `docs/ENV.md` · Signup: [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

Manual:

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

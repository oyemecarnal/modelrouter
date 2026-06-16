# OAuth connectors — stub (Phase 3)

**Status:** Not implemented. Phase 2 uses **paste-key** flows (`make connect-*`).

**Draft spec:** [`docs/OAUTH_CONNECTOR_SPEC.md`](OAUTH_CONNECTOR_SPEC.md) — security model, callback flow, acceptance criteria.

## Why deferred

- Paste-key covers homelab needs today (9 providers in `config/connectors.yaml`)
- OAuth needs token refresh, redirect URLs, and vault rules — separate security review
- Product question: self-host users may prefer paste-key over OAuth apps

## When we add it

1. Provider OAuth app registration (redirect to localhost or mini callback)
2. Token storage in kc-mini `.env` or 1Password — never git
3. Refresh job in gateway or cron
4. Widget "Connect with Google" vs terminal paste

## Until then

Use `make connect-provider` and `docs/WHY_MODELROUTER.md` for the value story.

See `docs/CONNECTOR_SPEC.md` for paste-key security model.

# OAuth connector spec (Phase 3 draft)

**Status:** Draft — not implemented. Phase 2 paste-key flows remain SSOT (`docs/CONNECTOR_SPEC.md`).

---

## Goal

Let users connect providers via OAuth (e.g. "Connect with Google") instead of pasting API keys — while keeping the same rule: **secrets live on kc-mini only**, never git or widget snapshots.

---

## Scope (MVP)

| In scope | Out of scope (later) |
|----------|----------------------|
| One provider pilot (likely Google/Gemini) | Full 9-provider OAuth matrix |
| Authorization code + refresh token on mini | Public multi-tenant SaaS OAuth |
| Widget button → localhost callback | Mobile / deep-link redirects |
| Token refresh cron or gateway hook | Per-user OAuth on shared homelab |

---

## Security model

| Rule | Implementation |
|------|----------------|
| Tokens never committed | Store in kc-mini `.env` or encrypted file; `.gitignore` |
| Tokens never in widget JSON | OAuth status LED only (`connected` / `expired` / `missing`) |
| Callback bound to localhost | `http://127.0.0.1:<port>/oauth/callback` on laptop or mini |
| CSRF | Random `state` param; validate on callback |
| Refresh before expiry | Cron or LiteLLM pre-call refresh; alert on `invalid_grant` |
| Revocation | `make disconnect-<provider>` clears env + revokes if API supports |

Paste-key validation rules in `modelrouter/env_store.py` do **not** apply to OAuth tokens — separate `oauth_store.py` module when built.

---

## Flow (authorization code)

```
Widget / CLI                ModelRouter (mini)              Provider
    │                              │                          │
    │  GET /oauth/start?provider=  │                          │
    │ ────────────────────────────►│                          │
    │  redirect URL + state        │                          │
    │ ◄────────────────────────────│                          │
    │  browser open authorize URL  │                          │
    │ ───────────────────────────────────────────────────────►│
    │  callback ?code=&state=      │                          │
    │ ────────────────────────────►│  exchange code           │
    │                              │ ────────────────────────►│
    │                              │  access + refresh token  │
    │                              │ ◄────────────────────────│
    │  204 / success LED           │  write mini .env         │
    │ ◄────────────────────────────│                          │
```

---

## Config (planned)

```yaml
# config/connectors.yaml (future)
google:
  mode: oauth  # vs paste_key today
  oauth:
    client_id_env: GOOGLE_OAUTH_CLIENT_ID
    client_secret_env: GOOGLE_OAUTH_CLIENT_SECRET
    scopes: [https://www.googleapis.com/auth/generative-language]
    token_env: GOOGLE_OAUTH_REFRESH_TOKEN
    redirect_port: 8766
```

CLI fallback while widget OAuth is WIP: keep `make connect-google` paste-key.

Dev callback stub (no token exchange):

```bash
OAUTH_STUB_LISTEN=1 make oauth-start PROVIDER=google
# listens http://127.0.0.1:8766/oauth/callback
```

---

## Human prerequisites

1. Register OAuth app at provider console (redirect URI = mini or laptop callback)
2. Set `GOOGLE_OAUTH_CLIENT_ID` / `SECRET` on kc-mini `.env` (not tower)
3. Decide callback host: laptop dev vs kc-mini production

---

## Acceptance criteria (when implemented)

- [ ] `make oauth-start PROVIDER=google` opens browser, completes callback
- [ ] Widget shows **Connected** LED without exposing token
- [ ] Refresh survives mini gateway restart
- [ ] `make audit-tower-wires` still passes (no OAuth tokens on tower)
- [ ] Paste-key path remains for air-gapped / no-browser setups

---

## Until then

- Paste-key: `make connect-provider` · widget **＋ Provider** modal
- Value story: `docs/WHY_MODELROUTER.md`
- Stub pointer: `docs/OAUTH_CONNECTOR_STUB.md`

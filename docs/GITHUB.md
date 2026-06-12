# GitHub structure

Repo: `oyemecarnal/modelrouter` (branch `main`)

## Layout

```
modelrouter/
├── VERSION              # Semver (iteration cycle bumps)
├── config/              # LiteLLM + homelab (hosts, projects, presets)
├── scripts/             # Ops (deploy, doctor, test, lint)
├── modelrouter/         # Python callbacks, route_policy, MCP
├── tokens/              # Keys widget (subproject)
├── docs/
│   ├── HOMELAB_GOALS.md
│   ├── iterations/      # 1.1–1.5 logs
│   └── ITERATION_REVIEW.md
├── .github/workflows/   # CI smoke
└── deploy/              # launchd plist
```

## Workflow

1. Dev on **laptop** → `make test` → `make lint`
2. `make deploy-mini` → kc-mini (rsync, no `.env`)
3. `make push-env-mini` for key sync (selected vars only)
4. Commit + push when ready; CI runs smoke on push

## Never commit

`.env`, `secrets.yaml`, `data/`, `.venv/`, `tokens/.env.local`

## Tags (optional)

After a cycle: `git tag v1.5.0 && git push origin v1.5.0`

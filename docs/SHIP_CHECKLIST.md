# Ship checklist

Use before **`/ship vX.Y.Z`** or manual commit. Automated gate: **`make ship-check`**.

## Automated

```bash
make ship-check          # test + lint + gateway SSOT check + optional smoke-routes
make sync-gateway-config # after editing policy_presets.yaml
make doctor-fix          # laptop gateway up (restart if needed)
make trim-logs           # if data/modelrouter.log grows large
make deploy-mini         # after commit — sync scripts to kc-mini
```

## Reject from git

- `.env`, `secrets.yaml`, `tokens/.env.local`
- `data/CORE_APIS.md`, `dist/*.tar.gz`
- Raw API keys in any file

## Capstone bundle (Cycles 19–21 example)

- [ ] `VERSION` matches `CHANGELOG` top section
- [ ] `docs/iterations/*.md` for the cycle
- [ ] `docs/ITERATION_REVIEW.md` ship status updated
- [ ] `make test` · `make lint` · `make audit-tower-wires`

## Post-ship homelab

```bash
make deploy-mini
make smoke-tower
make daemon-enable       # laptop — stable Cursor gateway
```

## Commands reference

| Command | When |
|---------|------|
| `/ship v3.40.0` | Commit + push (human/Cursor command) |
| `make sync-gateway-config` | Regenerate gateway YAML from policy_presets SSOT |
| `make connect-key PROVIDER=groq` | Unified paste-key connector |
| `make smoke-routes` | hermes-fast + hermes-smart on kc-mini |
| `make vault-bootstrap-alts-restart` | After pasting `__ALT_1` keys |
| `make vault-rotate-simulate-cleanup` | Test 429 rotate path (no API call) |
| `make enable-auto-rotate-mini-enable` | Auto 429 rotate on kc-mini |
| `make ensure-alt-slots` | Add empty `__ALT_1` lines in `.env` |
| `make dedupe-env-apply` | Remove duplicate `.env` keys |
| `make trim-logs` | Trim large `data/*.log` files |
| `make vault-scrape-collect` | Network key ingest → `data/key_vault.json` |
| `make vault-export` | Merge vault → `.env` |
| `make vault-rotate-export` | Apply last 429 rotate hint → `.env` |
| `make vault-rotate-push` | Rotate export + push keys to kc-mini |
| `make ship-check` | Pre-flight validation |
| `make doctor-fix` | Gateway down on laptop (`ensure-gateway`) |
| `make strip-tower-llm-keys` | Tower stray LLM keys |

See also: `.cursor/commands/ship.md`, `docs/CYCLES.md`.

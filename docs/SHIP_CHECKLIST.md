# Ship checklist

Use before **`/ship vX.Y.Z`** or manual commit. Automated gate: **`make ship-check`**.

## Automated

```bash
make ship-check          # test + lint + VERSION/CHANGELOG + tower audit
make ensure-gateway      # laptop gateway up (restart if needed)
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
| `/ship v3.22.0` | Commit + push (human/Cursor command) |
| `make ship-check` | Pre-flight validation |
| `make ensure-gateway` | Gateway down on laptop |
| `make strip-tower-llm-keys` | Tower stray LLM keys |

See also: `.cursor/commands/ship.md`, `docs/CYCLES.md`.

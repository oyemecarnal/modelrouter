---
description: ModelRouter hygiene — clutter, doc drift, quick validation
---

# /cleanup — ModelRouter

Repo-local prompt. Reference: `docs/CYCLES.md`.

## Goal

Practical hygiene so the homelab gateway repo stays easy to work in — without risky deletes or scope creep.

## Covenant

- Preserve unrelated user work.
- **Never commit** `.env`, `secrets.yaml`, `data/CORE_APIS.md`, `.venv`, or generated noise.
- Prefer documenting ambiguity over deleting config you do not understand.

## Process

1. Inspect `git status` and repo shape (~1 MB git; no mystery large artifacts).
2. Remove obvious junk: stale tmp, duplicate notes, broken comments, orphaned scripts.
3. Align short docs with reality — especially gateway URLs (`docs/HOSTS.md`), preset names, `make` targets in `README.md`.
4. Run relevant checks (not necessarily all):

```bash
make lint
make test
make doctor          # if gateway should be up
make remote-health   # mini reachability
```

5. Summarize what was cleaned; commit only if the human asked or the tree is clearly ready.

## ModelRouter hotspots

- `config/includes/policy_presets.yaml` vs `modelrouter.yaml` / `modelrouter.minimal.yaml` drift → `make check-presets`
- `models_catalog.yaml` drift → `make check-catalog`
- Stale iteration docs vs `VERSION`

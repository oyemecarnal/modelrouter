---
description: ModelRouter cleanup + validate + hand-off ready tree
---

# /cleanship — ModelRouter

Repo-local prompt. Reference: `docs/CYCLES.md`.

## Goal

Leave a **clean, validated, hand-off-ready** tree — the bridge between `/cleanup` or `/deepclean` and `/ship`.

## Covenant

- Small diffs; no secret commits; preserve unrelated user work.
- Docs must match `VERSION` and current homelab posture.

## Process

1. **Clean** — obvious clutter, doc drift, stale iteration notes (see `/cleanup` hotspots).
2. **Align docs** — `README.md`, `CHANGELOG.md`, `docs/HOMELAB_GOALS.md` human backlog, `docs/iterations/README.md` if cycle work landed.
3. **Validate core:**

```bash
make test
make lint
make check-presets
make check-catalog
```

4. **Gateway optional** (if daemon expected):

```bash
make restart && make health && make doctor
```

5. **Fix** anything validation broke; re-run until green or clearly document skips (e.g. gateway down, tower offline).
6. **Hand-off summary** — what changed, what checks passed, whether `/ship` + `make deploy-mini` is recommended.

## Do not stage

`.env`, `secrets.yaml`, `data/CORE_APIS.md`, `.venv/`

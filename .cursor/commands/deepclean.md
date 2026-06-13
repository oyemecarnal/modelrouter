---
description: ModelRouter deep maintenance — config drift, stale ops, cheap reliability fixes
---

# /deepclean — ModelRouter

Repo-local prompt. Reference: `docs/CYCLES.md`.

## Goal

Find accumulated drift — duplicate config, stale workflows, docs that lie about the homelab — and fix **cheap, low-risk** root causes.

## Covenant

- Tidy, not ambitious. No large refactors.
- **Never commit secrets.** Do not rotate master key without explicit human approval.
- When unsure about deletion, document or add a check script instead.

## Focus areas (ModelRouter)

| Area | Look for |
|------|----------|
| **Preset SSOT** | `policy_presets.yaml` copied into gateway YAMLs; `make check-presets` / `check-catalog` green |
| **Catalog caps** | `max_tokens` on primary routes; `make sync-preset-tokens` if drift |
| **Homelab URLs** | `config/hosts.yaml`, README, doctor — mDNS vs SSH alias confusion |
| **Ops scripts** | `start.sh` pidfile, `stop.sh` port cleanup, `healthcheck.sh` loopback on `0.0.0.0` |
| **Widget / tokens** | `fetch_usage.py`, snapshot paths, widget auth (`X-Widget-Token`) |
| **Docs** | `CLEAN_WIRES.md`, `HOMELAB_GOALS` human backlog, `PRODUCT_VISION` phase markers |
| **Artifacts** | `data/*.log`, stale pidfiles, accidental tracked generated files |

## Process

1. Read `docs/ITERATION_REVIEW.md` and recent `docs/iterations/` for known debt.
2. Fix or document each issue found.
3. Validate:

```bash
make lint && make test
make doctor || true
make homelab-status || true
```

4. Report: fixed, deferred, and whether `/cleanship` or `/ship` is the natural next step.

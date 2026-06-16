---
description: ModelRouter ship gate — verify, commit, push, deploy-mini when needed
---

# /ship — ModelRouter

Repo-local prompt. Reference: `docs/CYCLES.md`.

## Goal

Verify the tree, stage only intended changes, commit cleanly, push if appropriate, and **sync kc-mini** when the gateway or ops surface changed.

## Pre-flight (required)

```bash
git status
git diff
```

**Reject staging if present:** `.env`, `secrets.yaml`, `data/CORE_APIS.md`, full API keys, `.venv/`.

## Validation (required)

```bash
make ship-check   # test + lint + VERSION/CHANGELOG + tower audit
```

Or manually:

```bash
make test
make lint
```

**If `config/`, `scripts/`, `modelrouter/`, or `tokens/` changed:**

```bash
make doctor || make homelab-status
```

**If presets/catalog touched:**

```bash
make check-presets && make check-catalog
```

## Commit rules

- Commit only when the human asked, or this `/ship` command explicitly includes commit.
- Message reflects **why** (homelab ops, preset SSOT, widget, reliability, docs capstone).
- Capstone cycles: `VERSION` + `CHANGELOG` + `docs/iterations/X.Y.md` included.

See `docs/SHIP_CHECKLIST.md` for reject list and post-ship steps.

## Post-commit homelab

When gateway config, scripts, or widget changed:

```bash
make deploy-mini
```

Optional after key inventory changes:

```bash
make core-apis    # gitignored data/CORE_APIS.md
make keys-widget-fetch
```

## Master key warning

Do **not** rotate `MODELROUTER_MASTER_KEY` in a routine ship. Keep `crsr_*` unless human explicitly rewires Cursor.

## Output

- What shipped (files/themes)
- Check results
- Mini deploy status (ran / skipped / failed)
- Remaining human backlog items

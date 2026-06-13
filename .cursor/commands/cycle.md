---
description: ModelRouter full cycle — cleanup, deepclean, five iterations, lint/test, ship
---

# /cycle — ModelRouter (full global cycle)

**Repo-local override** of global `~/Dev/prompts/cycles.md`. Playbook: `docs/CYCLES.md`.

`/cycle` is the **umbrella command**. It runs the entire homelab workflow in order — the same substance as `/cleanup` → `/deepclean` → `/cleanship` → **five iterations** → `/cleanship` → `/ship` — in **one pass**. Do not skip phases unless a phase has nothing to do; say so explicitly.

## Context

**ModelRouter** — LiteLLM gateway on **kc-mini** (`http://Kevins-Mac-mini.local:3000`). Presets not vendors. Keys on mini. `docs/HOMELAB_GOALS.md` · `docs/iterations/` · `VERSION`.

## Covenant

- Ship small; preserve unrelated user work; ~1 MB git tree.
- **Never commit** `.env`, `secrets.yaml`, `data/CORE_APIS.md`, raw keys, `.venv`.
- **Do not rotate `MODELROUTER_MASTER_KEY`** unless human explicitly rewires Cursor (`crsr_*` stays).
- SSOT: `policy_presets.yaml` + `models_catalog.yaml`; `make sync-preset-tokens` when caps drift.
- OpenRouter stubbed; fail down (cheaper/local before expensive).

## Roles

**Lead** (orient + plan) → **Builder** (change) → **Reviewer** (regressions, secrets) → **Validator** (`make` targets) → **Closer** (document + ship).

---

## Full cycle pipeline (execute in order)

### Phase 0 — Orient

Read before touching code:

- `VERSION`, `git status`, `git diff`
- Latest `docs/iterations/*.md`, `docs/ITERATION_REVIEW.md`, `docs/COMMITTEE_REVIEW.md`
- Name the **next five iteration IDs** (e.g. 5.1–5.5) and whether this cycle ends in a capstone semver bump

---

### Phase 1 — `/cleanup` (hygiene)

**Goal:** Remove clutter; align docs with reality.

1. Inspect repo shape — no mystery artifacts, no tracked secrets.
2. Remove obvious junk; fix stale README/hosts/preset references.
3. Quick hotspots: preset SSOT drift, wrong LAN URLs (`Kevins-Mac-mini.local` HTTP; `kc-mini-lan` SSH-only).

**Validate (if anything changed):** `make lint`

---

### Phase 2 — `/deepclean` (drift)

**Goal:** Cheap fixes for accumulated drift.

Check and fix when cheap:

| Area | Action |
|------|--------|
| Presets | `make check-presets`, `make check-catalog` |
| Caps | `make sync-preset-tokens` if drift |
| Ops scripts | pidfile, `stop.sh`, health on `0.0.0.0` |
| Widget | snapshot auth, `fetch_usage.py` paths |
| Docs | `CLEAN_WIRES`, `HOMELAB_GOALS` human backlog |

Prefer document over risky delete.

**Validate (if anything changed):** `make lint`

---

### Phase 3 — `/cleanship` baseline (test + lint)

**Goal:** Confirm clean tree before iterations.

```bash
make test
make lint
make check-presets
make check-catalog
```

Fix anything broken before Phase 4. Gateway optional:

```bash
make doctor || true
```

---

### Phase 4 — Five iterations (`/i5` core)

**Goal:** Five bounded improvements toward next `docs/iterations/X.Y.md` (capstone **X.5** → `VERSION` + `CHANGELOG`).

**Priority order for choosing goals:**

1. security → 2. reliability → 3. correctness → 4. operability → 5. documentation → 6. cleanup

**Per iteration (repeat ×5):**

1. **One clear goal** — smallest safe change.
2. **Build** — match conventions in `scripts/`, `config/`, `modelrouter/`, `tokens/`.
3. **Validate immediately:**

| Touch | Run |
|-------|-----|
| shell / yaml / config | `make lint` |
| code / routing / widget | `make test` |
| gateway / daemon / deploy | `make restart` → `make health` → `make doctor` |
| homelab | `make homelab-status` or `make remote-health` |
| catalog / presets | `make check-catalog`, `make check-presets` |
| keys / routing | `make cost-review` (no full keys in output) |

4. **Document** — update `docs/iterations/X.Y.md` for that iteration.

If repo is already healthy for an iteration slot, use it for docs, validation, or drift — do not invent churn.

---

### Phase 5 — `/cleanship` final (post-iteration)

**Goal:** Hand-off-ready tree after all five iterations.

1. Align `README.md`, `CHANGELOG.md`, `docs/iterations/README.md` if capstone landed.
2. Full validation:

```bash
make test
make lint
make check-presets
make check-catalog
```

3. Homelab posture (when gateway/ops touched):

```bash
make homelab-status || make doctor || true
```

4. Fix regressions; re-run until green or document skips.

---

### Phase 6 — `/ship` (close)

**Goal:** Verify, commit, push, sync mini.

**Pre-flight:**

```bash
git status
git diff
```

Reject staging: `.env`, `secrets.yaml`, `data/CORE_APIS.md`, `.venv/`.

**Ship gate:**

```bash
make test && make lint
```

Commit **only when human asked or this cycle explicitly includes ship**. Message = why, not file list.

**Post-commit homelab** (when `config/`, `scripts/`, `modelrouter/`, or `tokens/` changed):

```bash
make deploy-mini
```

Optional: `make core-apis`, `make keys-widget-fetch`.

---

## Output contract (required)

Report every phase, even if skipped:

| Section | Content |
|---------|---------|
| **0 Orient** | VERSION, branch, five iteration IDs planned |
| **1 Cleanup** | what was cleaned or "nothing needed" |
| **2 Deepclean** | drift fixed or "nothing needed" |
| **3 Baseline** | test/lint/check results |
| **4 Iterations** | each of 5: goal → change → validation |
| **5 Final cleanship** | test/lint/doctor/homelab results |
| **6 Ship** | committed/pushed/deployed or deferred + why |
| **Health table** | test · lint · presets · catalog · doctor · mini |
| **Deferred** | tower, Cursor URL, key rotation, salt, etc. |
| **Verdict** | **shipped** / **ready to ship** / **continue next cycle** |

## Human backlog (flag only)

Cursor → ModelRouter URL · `push-client-env-tower` · Anthropic on mini · Groq rotation if exposed.

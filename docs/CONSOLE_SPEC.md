# Console MVP spec (Phase 1)

**Status:** Read-only static grid — no OAuth, no key editing.  
**Seed:** Keys widget ([`tokens/widget/index.html`](../tokens/widget/index.html)).

## Goal

One glance answers: **which presets/models exist, what they cost, who uses them, are they reachable?**

## Data sources

| Source | Fields |
|--------|--------|
| [`config/models_catalog.yaml`](../config/models_catalog.yaml) | preset labels, cost_tier, max_tokens, clients; model context_window, provider |
| [`config/projects.yaml`](../config/projects.yaml) | project → preset mapping |
| Widget snapshot `policyPresets` | [`tokens/scripts/preset_catalog.py`](../tokens/scripts/preset_catalog.py) |
| Widget snapshot `consoleGrid` | [`tokens/scripts/console_grid.py`](../tokens/scripts/console_grid.py) |
| Gateway `/v1/models` (optional live) | registered model ids when gateway up |

## UI layout (widget section: **Console**)

```
┌─ Console ─────────────────────────────────────┐
│ Presets (policy)                              │
│  cheap      free_low   4096 tok  kalshi,…     │
│  hermes-fast free_low  4096 tok  smalshi      │
│ …                                             │
│ Models (provider routes)                      │
│  groq/llama-3.1-8b-instant  131k ctx  free_low│
│  openai/gpt-4o              128k ctx  high    │
│ …                                             │
│ Gateway: 12 models registered (live) | cached │
└───────────────────────────────────────────────┘
```

## Non-goals (defer)

- Add provider / OAuth
- Edit presets or caps in UI
- Per-project spend enforcement (needs Postgres)

## Commands

```bash
make keys-widget-fetch   # refreshes snapshot with consoleGrid
make usage-rollup        # log-based metering summary
```

## Future (Phase 1.5+)

- Standalone static page under `tokens/console/`
- Click preset → copy model name for client config
- Live green/gray/red from health per provider route

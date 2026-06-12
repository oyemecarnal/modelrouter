# API Key Inventory

**Live private list:** `data/CORE_APIS.md` (gitignored — regenerate with `make core-apis`).

That file merges:
- `config/api_catalog.yaml` (families, signup links, pricing hints)
- `config/models_catalog.yaml` (gateway presets)
- `config/projects.yaml` (project → preset mapping)
- Laptop `.env` + kc-mini `.env` key **names** (masked values only)
- Optional `data/inventory_snapshot.json` disk locations

## Quick commands

```bash
make core-apis        # refresh private CORE_APIS.md
make keys-audit       # ./scripts/discover-keys.sh (masked)
make inventory        # machine scan
make inventory-mini   # same on kc-mini
```

## Security

1. Never commit `data/CORE_APIS.md` or `.env`
2. kc-mini is the secrets hub — `make push-env-mini` after laptop changes
3. Provider keys belong on gateway host only — see `docs/CLEAN_WIRES.md`

## Catalog source of truth

Editable committed catalog: `config/api_catalog.yaml` (widget ◎ Assess, cost compare, key add UI).

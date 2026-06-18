# Laptop gateway daemon (launchd)

Keep ModelRouter running on the **laptop** so Cursor always hits `http://127.0.0.1:3000/v1` without manual `make restart`.

Production agents use **kc-mini** — see `docs/TOWER_WIRING.md`. This doc is for **local dev + Cursor**.

## Enable auto-start

```bash
cd ~/dev/modelrouter
make daemon-enable    # install com.modelrouter.plist via launchd (bootstrap on modern macOS)
make health           # confirm gateway up
make smoke-cursor     # Cursor path check
```

## Disable

```bash
make daemon-disable
```

## When gateway is down

Symptoms: `make test` skips health, `make smoke-cursor` fails, widget PATHS LEDs red.

```bash
make status           # PID + health
make doctor-fix       # restart if down (alias: make ensure-gateway)
make restart          # stop + start daemon
make logs             # tail modelrouter.log
```

If port 3000 is stuck:

```bash
make stop
lsof -i :3000         # should be empty
make daemon
```

## launchd plist

Installed from `deploy/com.modelrouter.plist` by `scripts/start-daemon.sh` when `make daemon-enable` runs.

Logs: `data/modelrouter.log` · Pidfile reconciled from port listener (`modelrouter_reconcile_pidfile`).

## Cursor wiring

See `docs/CURSOR_WIRING.md` — base URL `http://127.0.0.1:3000/v1`, bearer `MODELROUTER_MASTER_KEY` (`crsr_*` OK).

## Mini vs laptop

| Host | Daemon | URL |
|------|--------|-----|
| Laptop | `make daemon-enable` | `http://127.0.0.1:3000` |
| gateway-mini | `make daemon-enable` on gateway host | `gateway.url` from `config/hosts.yaml` |

Provider keys stay on **mini** for production; laptop `.env` is for dev + `make push-env-mini`.

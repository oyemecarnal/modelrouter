# Homelab hosts configuration

ModelRouter ships a **generic** `config/hosts.yaml` safe to publish. Your real hostnames, Tailscale IPs, and SSH aliases belong in a local overlay.

## Quick setup

```bash
cp config/hosts.local.yaml.example config/hosts.local.yaml
# Edit gateway.url, gateway.url_tailscale, and ssh Host aliases
```

`config/hosts.local.yaml` is gitignored. Scripts and the keys widget prefer it over `config/hosts.yaml` when present.

## Environment overrides

| Variable | Purpose |
|----------|---------|
| `MODELROUTER_MINI_URL` | Override LAN gateway URL for smoke tests and health checks |
| `MODELROUTER_REMOTE_DIR` | Remote deploy path (default `$HOME/dev/modelrouter`) |
| `MODELROUTER_REMOTE_HOST` | SSH target for `make deploy-mini` (overrides `hosts.yaml` gateway-mini ssh) |
| `KC_TOWER_SSH` | SSH alias for tower probes (`gateway-tower`, etc.) |

## Gateway URLs

| Field | Use |
|-------|-----|
| `gateway.url` | mDNS / LAN HTTP — laptops and macOS agents |
| `gateway.url_tailscale` | Tailscale IP — Linux hosts without mDNS |
| `gateway.url_local` | Laptop dev (`127.0.0.1:3000`) |
| `gateway.url_ssh_alias` | Documentation only — SSH Host names are not HTTP endpoints |

Remote runtime hosts should use `config/client.env.example` with the URL that works from that machine.

## SSH config

Add Host entries in `~/.ssh/config` matching the names in `hosts.yaml` / `hosts.local.yaml`:

```
Host gateway-mini
  HostName your-mini.local
  User you

Host gateway-tower
  HostName 100.x.x.x
  User you
```

See also: `docs/TOWER_WIRING.md`, `docs/LAPTOP_DAEMON.md`, `make homelab-status`.

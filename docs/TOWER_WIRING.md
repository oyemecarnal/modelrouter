# Remote runtime → ModelRouter gateway

Runtime hosts (Linux agents, bots) call the **always-on gateway host** only. No provider keys on remote machines.

## Gateway URL

| From | URL |
|------|-----|
| **Linux runtime** (no mDNS) | `gateway.url_tailscale` from `config/hosts.yaml` |
| **macOS / LAN** | `gateway.url` (mDNS or static hostname) |

Customize in `config/hosts.local.yaml` — see `docs/HOSTS.md`.

## Client env

```bash
make push-client-env-tower   # writes ~/.config/modelrouter/client.env on runtime host
make smoke-tower             # hermes-fast + cheap from remote host
```

Agents: `source ~/.config/modelrouter/client.env` — presets in `config/projects.yaml`.

## SSH

Set `KC_TOWER_SSH` to your runtime host alias (`gateway-tower`, etc.) in `~/.ssh/config`. Tailscale or LAN must be reachable from the operator laptop.

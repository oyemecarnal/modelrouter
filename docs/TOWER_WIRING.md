# kc-tower → ModelRouter

Tower agents call **kc-mini** only. No provider keys on tower.

## Gateway URL

| From | URL |
|------|-----|
| **kc-tower** (Linux) | `http://100.85.245.23:3000/v1` (mini Tailscale — mDNS does not resolve) |
| Laptop / macOS LAN | `http://Kevins-Mac-mini.local:3000/v1` |

SSOT: `config/hosts.yaml` → `gateway.url_tailscale`

## Client env

```bash
make push-client-env-tower   # writes ~/.config/modelrouter/client.env on tower
make smoke-tower             # hermes-fast + cheap from tower
```

Hermes/Kalshi/coinbot: `source ~/.config/modelrouter/client.env` — presets in `config/projects.yaml`.

## SSH

Prefer **`ssh kc-tower`** (Tailscale `100.116.94.38`). `kc-tower-lan` uses ProxyJump via mini and is a fallback only.

Tailscale must be running on laptop and tower.

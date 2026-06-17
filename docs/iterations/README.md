# Iteration log

Five quick iterations per cycle. Each version: small change → test → doc.

| Version | Focus | Doc |
|---------|--------|-----|
| 1.1 | Versioning + homelab charter + `make test` | [1.1.md](1.1.md) |
| 1.2 | `config/hosts.yaml` + remote health | [1.2.md](1.2.md) |
| 1.3 | GitHub structure + CI | [1.3.md](1.3.md) |
| 1.4 | Lint harness | [1.4.md](1.4.md) |
| 1.5 | `make homelab-status` + integration | [1.5.md](1.5.md) |

## Cycle 2 (Phase 0 completion)

| Version | Focus | Doc |
|---------|--------|-----|
| 2.1 | Clean wires: fail-closed, client.env, key refresh | [2.1.md](2.1.md) |
| 2.2 | Daemon throttle + deploy remote-health | [2.2.md](2.2.md) |
| 2.3 | Preset SSOT check in test | [2.3.md](2.3.md) |
| 2.4 | `make consolidate-keys` | [2.4.md](2.4.md) |
| 2.5 | Committee bug fixes + widget auth → **v2.5.0** | [2.5.md](2.5.md) |

After each cycle: read `docs/ITERATION_REVIEW.md` (AI synthesis).

## Cycle 3 (reliability + Phase 0 tail)

| Version | Focus | Doc |
|---------|--------|-----|
| 3.1 | Daemon pid, health bind, salt warn, doc URL sync | [3.1.md](3.1.md) |
| 3.2 | `stop.sh` port cleanup; doctor no crash when down | [3.2.md](3.2.md) |
| 3.3 | `deploy-mini` — mini on 3.x | [3.3.md](3.3.md) |
| 3.4 | Committee checkpoint + clean-wires docs | [3.4.md](3.4.md) |
| 3.5 | Cycle capstone → **v3.0.0** | [3.5.md](3.5.md) |

## Cycle 4 (Phase 1 — catalog & calibration)

| Version | Focus | Doc |
|---------|--------|-----|
| 4.1 | `models_catalog.yaml` + salt rotate → **v3.1.0** | [4.1.md](4.1.md) |
| 4.2 | `make core-apis` private live API list → **v3.2.0** | [4.2.md](4.2.md) |
| 4.3 | Preset catalog in widget snapshot | [4.3.md](4.3.md) |
| 4.4 | Widget policy presets UI | [4.4.md](4.4.md) |
| 4.5 | `max_tokens` sync + ops hints → **v3.5.0** | [4.5.md](4.5.md) |

## Cycle 5 (Phase 1 tail — validation & agent ops)

| Version | Focus | Doc |
|---------|--------|-----|
| 5.1 | Test harness hardening | [5.1.md](5.1.md) |
| 5.2 | Doc drift — LAN URL in ITERATION_REVIEW | [5.2.md](5.2.md) |
| 5.3 | PRODUCT_VISION Phase 1 max_tokens done | [5.3.md](5.3.md) |
| 5.4 | CHANGELOG + cycles playbook | [5.4.md](5.4.md) |
| 5.5 | Full `/cycle` validate + ship gate | [5.5.md](5.5.md) |

## Cycle 6 (clean wires + Console MVP)

| Version | Focus | Doc |
|---------|--------|-----|
| 6.1 | `smoke-cursor` + `CURSOR_WIRING.md` | [6.1.md](6.1.md) |
| 6.2 | `smoke-tower` + homelab tower row | [6.2.md](6.2.md) |
| 6.3 | `check-key-hygiene` + `KEY_ROTATION.md` + push-env-mini | [6.3.md](6.3.md) |
| 6.4 | `CONSOLE_SPEC.md` + widget Console grid | [6.4.md](6.4.md) |
| 6.5 | `usage-rollup` + ship → **v3.6.0** | [6.5.md](6.5.md) |

## Cycle 7 (Phase 0/1 capstone — calibration ops)

| Version | Focus | Doc |
|---------|--------|-----|
| 7.1 | Snapshot export security guard in `test.sh` | [7.1.md](7.1.md) |
| 7.2 | Test harness pidfile reconcile before health | [7.2.md](7.2.md) |
| 7.3 | `context_window` catalog check + `CONTEXT_GUIDE.md` | [7.3.md](7.3.md) |
| 7.4 | `usage-rollup` in `homelab-status` + doctor hints | [7.4.md](7.4.md) |
| 7.5 | Phase markers + ship → **v3.7.0** | [7.5.md](7.5.md) |

## Cycle 8 (Phase 2 — Groq connector MVP)

| Version | Focus | Doc |
|---------|--------|-----|
| 8.1 | `CONNECTOR_SPEC.md` security model | [8.1.md](8.1.md) |
| 8.2 | `env_store.py` atomic `.env` writes | [8.2.md](8.2.md) |
| 8.3 | Groq key validation + test smoke | [8.3.md](8.3.md) |
| 8.4 | `make connect-groq` end-to-end ops | [8.4.md](8.4.md) |
| 8.5 | Phase 2 markers + ship → **v3.8.0** | [8.5.md](8.5.md) |

## Cycle 9 (Anthropic connector + receiver bar)

| Version | Focus | Doc |
|---------|--------|-----|
| 9.1 | Connector script checks + Anthropic validation in `test.sh` | [9.1.md](9.1.md) |
| 9.2 | `make connect-anthropic` + `docs/ENV.md` | [9.2.md](9.2.md) |
| 9.3 | Widget receiver — 5 presets, 3 LED rows | [9.3.md](9.3.md) |
| 9.4 | `homelab_status` + webhook network probes | [9.4.md](9.4.md) |
| 9.5 | Docs sync + ship → **v3.9.0** | [9.5.md](9.5.md) |

## Cycle 10 (connector registry + hermes-smart smoke)

| Version | Focus | Doc |
|---------|--------|-----|
| 10.1 | `connectors.yaml` registry validation in `test.sh` | [10.1.md](10.1.md) |
| 10.2 | `make smoke-hermes-smart` | [10.2.md](10.2.md) |
| 10.3 | Registry ↔ `connect-{id}.sh` mapping | [10.3.md](10.3.md) |
| 10.4 | Ops docs — `connect-provider`, smoke hints | [10.4.md](10.4.md) |
| 10.5 | Capstone + ship → **v3.10.0** | [10.5.md](10.5.md) |

## Cycle 11 (tower audit + OpenAI connector)

| Version | Focus | Doc |
|---------|--------|-----|
| 11.1 | `make audit-tower-wires` — no secret print | [11.1.md](11.1.md) |
| 11.2 | Hygiene hook + non-blocking tower SSH | [11.2.md](11.2.md) |
| 11.3 | `make connect-openai` + registry | [11.3.md](11.3.md) |
| 11.4 | README positioning + ops docs | [11.4.md](11.4.md) |
| 11.5 | Capstone → **v3.11.0** | [11.5.md](11.5.md) |

## Cycle 12 (landing + Mistral + registry LEDs)

| Version | Focus | Doc |
|---------|--------|-----|
| 12.1 | Audit `client.env` gateway-key whitelist | [12.1.md](12.1.md) |
| 12.2 | `make clean-tower-wires` | [12.2.md](12.2.md) |
| 12.3 | `make connect-mistral` | [12.3.md](12.3.md) |
| 12.4 | Registry-driven receiver LEDs + `LANDING.md` | [12.4.md](12.4.md) |
| 12.5 | Capstone → **v3.12.0** | [12.5.md](12.5.md) |

## Cycle 13 (Google connector + signup links)

| Version | Focus | Doc |
|---------|--------|-----|
| 13.1 | `GOOGLE_API_KEY` validation | [13.1.md](13.1.md) |
| 13.2 | `docs/TOWER_CLEANUP.md` + audit hints | [13.2.md](13.2.md) |
| 13.3 | `make connect-google` | [13.3.md](13.3.md) |
| 13.4 | Widget signup links from registry | [13.4.md](13.4.md) |
| 13.5 | Capstone → **v3.13.0** | [13.5.md](13.5.md) |

## Cycle 14 (DeepSeek/Together + Add Provider + daemon docs)

| Version | Focus | Doc |
|---------|--------|-----|
| 14.1 | DeepSeek/Together key validation | [14.1.md](14.1.md) |
| 14.2 | `docs/LAPTOP_DAEMON.md` | [14.2.md](14.2.md) |
| 14.3 | `connect-deepseek`, `connect-together` | [14.3.md](14.3.md) |
| 14.4 | Widget **＋ Provider** menu | [14.4.md](14.4.md) |
| 14.5 | Capstone → **v3.14.0** | [14.5.md](14.5.md) |

## Cycle 19 (why doc + wire exceptions)

| Version | Focus | Doc |
|---------|--------|-----|
| 19.1 | `docs/WHY_MODELROUTER.md` | [19.1.md](19.1.md) |
| 19.2 | `config/wire_exceptions.yaml` | [19.2.md](19.2.md) |
| 19.3 | Exception schema in `test.sh` | [19.3.md](19.3.md) |
| 19.4 | README / backlog links | [19.4.md](19.4.md) |
| 19.5 | OAuth stub + **v3.19.0** | [19.5.md](19.5.md) |

## Cycle 20 (paste modal + tower strip)

| Version | Focus | Doc |
|---------|--------|-----|
| 20.1 | Audit `.env.*` + `strip-tower-llm-keys` | [20.1.md](20.1.md) |
| 20.2 | Doctor gateway-down fix block | [20.2.md](20.2.md) |
| 20.3 | Widget paste modal + API | [20.3.md](20.3.md) |
| 20.4 | `connector_paste` tests | [20.4.md](20.4.md) |
| 20.5 | Capstone **v3.20.0** | [20.5.md](20.5.md) |

## Cycle 21 (OAuth draft + gateway hints)

| Version | Focus | Doc |
|---------|--------|-----|
| 21.1 | `OAUTH_CONNECTOR_SPEC.md` | [21.1.md](21.1.md) |
| 21.2 | Gateway-down hints (homelab + cost) | [21.2.md](21.2.md) |
| 21.3 | Widget push/restart toggles | [21.3.md](21.3.md) |
| 21.4 | Widget hints render + tests | [21.4.md](21.4.md) |
| 21.5 | Capstone **v3.21.0** | [21.5.md](21.5.md) |

## Cycle 22 (ship gate + ensure-gateway)

| Version | Focus | Doc |
|---------|--------|-----|
| 22.1 | `make ensure-gateway` | [22.1.md](22.1.md) |
| 22.2 | OAuth stub + callback listener | [22.2.md](22.2.md) |
| 22.3 | `make ship-check` | [22.3.md](22.3.md) |
| 22.4 | `SHIP_CHECKLIST.md` | [22.4.md](22.4.md) |
| 22.5 | Capstone **v3.22.0** | [22.5.md](22.5.md) |

## Cycle 23 (portfolio + key vault + themes)

| Version | Focus | Doc |
|---------|--------|-----|
| 23.1 | Portfolio equity + Kalshi + key vault + themes → **v3.23.0** | [23.1.md](23.1.md) |

## Cycle 24 (widget reliability + vault ops)

| Version | Focus | Doc |
|---------|--------|-----|
| 24.1 | Vault masked export tests | [24.1.md](24.1.md) |
| 24.2 | Equity fetch timeout + stale cache | [24.2.md](24.2.md) |
| 24.3 | Stale equity flag correctness | [24.3.md](24.3.md) |
| 24.4 | Doctor + homelab vault hints | [24.4.md](24.4.md) |
| 24.5 | Capstone **v3.24.0** | [24.5.md](24.5.md) |

## Cycle 25 (vault export guard + route key hints)

| Version | Focus | Doc |
|---------|--------|-----|
| 25.1 | Vault export deny | [25.1.md](25.1.md) |
| 25.2 | Route key hints | [25.2.md](25.2.md) |
| 25.3 | Tangem env template | [25.3.md](25.3.md) |
| 25.4 | `make doctor-fix` | [25.4.md](25.4.md) |
| 25.5 | Capstone **v3.25.0** | [25.5.md](25.5.md) |

## Cycle 26 (429 rotate + vault widget + OAuth exchange)

| Version | Focus | Doc |
|---------|--------|-----|
| 26.1 | OAuth state + exchange gate | [26.1.md](26.1.md) |
| 26.2 | 429 → vault rotate hints | [26.2.md](26.2.md) |
| 26.3 | Widget vault toggle UI | [26.3.md](26.3.md) |
| 26.4 | OAuth callback + doctor hints | [26.4.md](26.4.md) |
| 26.5 | Capstone **v3.26.0** | [26.5.md](26.5.md) |

## Cycle 27 (Tangem ETH + rotate export + daemon fix)

| Version | Focus | Doc |
|---------|--------|-----|
| 27.1 | launchd bootstrap | [27.1.md](27.1.md) |
| 27.2 | Widget SSL / venv path | [27.2.md](27.2.md) |
| 27.3 | ETH RPC fallback | [27.3.md](27.3.md) |
| 27.4 | vault-rotate-export | [27.4.md](27.4.md) |
| 27.5 | Capstone **v3.27.0** | [27.5.md](27.5.md) |

## Cycle 28 (alt Groq routes + auto rotate + push)

| Version | Focus | Doc |
|---------|--------|-----|
| 28.1 | Auto-rotate gate | [28.1.md](28.1.md) |
| 28.2 | Groq __ALT_1 routes | [28.2.md](28.2.md) |
| 28.3 | rotate_export log | [28.3.md](28.3.md) |
| 28.4 | vault-rotate-push | [28.4.md](28.4.md) |
| 28.5 | Capstone **v3.28.0** | [28.5.md](28.5.md) |

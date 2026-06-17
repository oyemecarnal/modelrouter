"""
Network key vault — scrape homelab hosts, store multi-key inventory, export centralized .env.

Security:
  - Default scrape is discovery (masked metadata) unless --collect and policy allows
  - Secrets only in data/key_vault.json (gitignored via data/)
  - Never prints raw values in CLI (masked fingerprints only)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modelrouter.env_store import validate_provider_key
from modelrouter.machine_inventory import (
    ENV_LINE,
    InventoryReport,
    expand,
    load_config as load_inventory_config,
    mask_value,
    scrape as scrape_inventory,
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "key_vault.yaml"
VAULT_VERSION = 1

ENV_LINE_EXPORT = re.compile(r"^(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=\s*(.+)$")


@dataclass
class VaultEntry:
    id: str
    env_var: str
    value: str
    fingerprint: str
    source_host: str
    source_path: str
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    priority: int = 50
    collected_at: str = ""
    last_used_at: str | None = None
    use_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VaultEntry:
        return cls(
            id=data["id"],
            env_var=data["env_var"],
            value=data["value"],
            fingerprint=data["fingerprint"],
            source_host=data["source_host"],
            source_path=data["source_path"],
            enabled=data.get("enabled", True),
            tags=list(data.get("tags") or []),
            priority=int(data.get("priority") or 50),
            collected_at=data.get("collected_at") or "",
            last_used_at=data.get("last_used_at"),
            use_count=int(data.get("use_count") or 0),
        )


def load_vault_config(path: Path | None = None) -> dict[str, Any]:
    import yaml

    p = path or DEFAULT_CONFIG
    return yaml.safe_load(p.read_text()) or {}


def vault_path(cfg: dict[str, Any]) -> Path:
    rel = cfg.get("vault_file") or "data/key_vault.json"
    p = Path(rel)
    return p if p.is_absolute() else ROOT / p


def fingerprint(value: str) -> str:
    v = (value or "").strip()
    if len(v) <= 12:
        h = hashlib.sha256(v.encode()).hexdigest()[:8]
        return f"hash:{h}"
    return mask_value(v)


def value_hash(value: str) -> str:
    return hashlib.sha256(value.strip().encode()).hexdigest()


def _permissions(cfg: dict[str, Any]) -> dict[str, Any]:
    return cfg.get("permissions") or {}


def _can_collect_var(env_var: str, host_id: str, cfg: dict[str, Any]) -> bool:
    perms = _permissions(cfg)
    if env_var in set(perms.get("deny_vars") or []):
        return False
    if host_id in set(perms.get("deny_collect_hosts") or []):
        return False
    opt_in = perms.get("opt_in") or {}
    if env_var in set(perms.get("require_opt_in") or []):
        return bool(opt_in.get(env_var))
    return bool(perms.get("collect_values", False))


def _service_for_var(env_var: str, cfg: dict[str, Any]) -> dict[str, Any] | None:
    for _sid, svc in (cfg.get("services") or {}).items():
        if env_var == svc.get("env_var"):
            return svc
        if env_var in (svc.get("aliases") or []):
            return svc
    return None


def _looks_like_secret_value(env_var: str, val: str) -> bool:
    v = (val or "").strip()
    if not v or len(v) < 12:
        return False
    if any(ch in v for ch in ("$", "`", "\n", "\r")):
        return False
    if v.startswith("op://"):
        return False
    err = validate_provider_key(env_var, v)
    if err:
        # Allow vars without strict patterns if long enough and alphanumeric-ish
        if err.endswith("too short"):
            return False
        known = env_var in {
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY", "GOOGLE_API_KEY",
            "MISTRAL_API_KEY", "DEEPSEEK_API_KEY", "TOGETHER_API_KEY", "FIREWORKS_API_KEY",
            "COHERE_API_KEY",
        }
        if known:
            return False
    return True


def _skip_source_path(path: str) -> bool:
    p = path.replace("\\", "/")
    skip_fragments = (
        "/scripts/connect-",
        "/scripts/vault-",
        "/node_modules/",
        ".example",
        ".template",
    )
    return any(s in p for s in skip_fragments)


def _read_env_key(path: Path, key: str) -> str | None:
    try:
        text = path.read_text(errors="ignore")
    except OSError:
        return None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = ENV_LINE_EXPORT.match(s)
        if m and m.group(1) == key:
            return m.group(2).strip().strip("'\"")
    return None


def _parse_env_file(path: Path, host_id: str, cfg: dict[str, Any], *, collect: bool) -> list[VaultEntry]:
    entries: list[VaultEntry] = []
    inv_cfg = load_inventory_config(expand(str((cfg.get("hosts") or {}).get("laptop", {}).get("inventory_config") or "config/inventory.yaml")))
    allowed_names = set(inv_cfg.get("api_key_names") or [])
    try:
        text = path.read_text(errors="ignore")
    except OSError:
        return entries

    rel = str(path)
    try:
        rel = str(path.relative_to(Path.home()))
    except ValueError:
        pass

    now = datetime.now(timezone.utc).isoformat()
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = ENV_LINE_EXPORT.match(s)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip().strip("'\"")
        if key not in allowed_names and not key.endswith("_API_KEY") and "TOKEN" not in key:
            continue
        if not val or val.startswith("op://"):
            continue
        if _skip_source_path(rel):
            continue
        if collect and not _can_collect_var(key, host_id, cfg):
            continue
        if not collect:
            continue
        if not _looks_like_secret_value(key, val):
            continue
        svc = _service_for_var(key, cfg)
        tags = list(svc.get("tags") or []) if svc else []
        entries.append(
            VaultEntry(
                id=uuid.uuid4().hex[:12],
                env_var=key,
                value=val,
                fingerprint=fingerprint(val),
                source_host=host_id,
                source_path=rel,
                enabled=True,
                tags=tags,
                priority=80 if host_id == "kc-mini" else 60,
                collected_at=now,
            )
        )
    return entries


def _ssh_read_env_file(ssh: str, remote_path: str, host_id: str, cfg: dict[str, Any], *, collect: bool) -> list[VaultEntry]:
    if not collect:
        return []
    host_cfg = (cfg.get("hosts") or {}).get(host_id) or {}
    if not host_cfg.get("collect", True):
        return []
    proc = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=8", ssh, f"test -f '{remote_path}' && cat '{remote_path}'"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    tmp = Path(f"/tmp/key_vault_{host_id}_{uuid.uuid4().hex}.env")
    try:
        tmp.write_text(proc.stdout)
        return _parse_env_file(tmp, host_id, cfg, collect=True)
    finally:
        tmp.unlink(missing_ok=True)


def scrape_host(host_id: str, cfg: dict[str, Any], *, collect: bool) -> tuple[InventoryReport | None, list[VaultEntry]]:
    hosts = cfg.get("hosts") or {}
    host_cfg = hosts.get(host_id)
    if not host_cfg:
        raise ValueError(f"Unknown host: {host_id}")

    entries: list[VaultEntry] = []
    report: InventoryReport | None = None
    htype = host_cfg.get("type", "local")

    if htype == "local":
        inv_path = expand(str(host_cfg.get("inventory_config") or "config/inventory.yaml"))
        inv_cfg = load_inventory_config(inv_path)
        report = scrape_inventory(inv_cfg)
        if collect and host_cfg.get("collect", True):
            for finding in report.api_findings:
                if finding.kind not in ("env", "wallet_env"):
                    continue
                path = expand(f"~/{finding.path}") if not finding.path.startswith("/") else Path(finding.path)
                if not path.is_file():
                    path = Path.home() / finding.path
                val = _read_env_key(path, finding.name)
                if not val or not _can_collect_var(finding.name, host_id, cfg):
                    continue
                if _skip_source_path(finding.path):
                    continue
                if not _looks_like_secret_value(finding.name, val):
                    continue
                svc = _service_for_var(finding.name, cfg)
                entries.append(
                    VaultEntry(
                        id=uuid.uuid4().hex[:12],
                        env_var=finding.name,
                        value=val,
                        fingerprint=fingerprint(val),
                        source_host=host_id,
                        source_path=finding.path,
                        enabled=True,
                        tags=list(svc.get("tags") or []) if svc else [],
                        priority=70,
                        collected_at=datetime.now(timezone.utc).isoformat(),
                    )
                )
    elif htype == "ssh":
        ssh = host_cfg.get("ssh") or host_id
        if collect and host_cfg.get("collect", False):
            for remote in host_cfg.get("env_files") or []:
                entries.extend(_ssh_read_env_file(ssh, remote, host_id, cfg, collect=True))
        # Masked discovery via remote inventory when available
        remote_dir = host_cfg.get("remote_dir") or "/Users/kevinreed/dev/modelrouter"
        proc = subprocess.run(
            [
                "ssh",
                "-o",
                "ConnectTimeout=8",
                ssh,
                f"cd '{remote_dir}' && PYTHONPATH=. .venv/bin/python -m modelrouter.machine_inventory 2>/dev/null || true",
            ],
            capture_output=True,
            text=True,
            timeout=45,
        )
        if proc.stdout.strip():
            report = InventoryReport(
                host=f"{host_id} ({ssh})",
                scanned_at=datetime.now(timezone.utc).isoformat(),
            )
    return report, entries


def scrape_network(cfg: dict[str, Any] | None = None, *, collect: bool = False, host: str | None = None) -> dict[str, Any]:
    cfg = cfg or load_vault_config()
    host_ids = [host] if host else list((cfg.get("hosts") or {}).keys())
    all_entries: list[VaultEntry] = []
    reports: dict[str, Any] = {}

    for hid in host_ids:
        try:
            report, entries = scrape_host(hid, cfg, collect=collect)
            if report:
                reports[hid] = report.to_dict() if hasattr(report, "to_dict") else {}
            all_entries.extend(entries)
        except Exception as exc:
            reports[hid] = {"error": str(exc)[:200]}

    merged = merge_entries(load_vault(cfg), all_entries, cfg)
    save_vault(cfg, merged)
    return {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "collect": collect,
        "hosts": host_ids,
        "new_entries": len(all_entries),
        "total_entries": len(merged.get("keys") or []),
        "reports": reports,
    }


def load_vault(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or load_vault_config()
    path = vault_path(cfg)
    if not path.exists():
        return {"version": VAULT_VERSION, "updated_at": "", "keys": []}
    try:
        data = json.loads(path.read_text())
        data.setdefault("keys", [])
        return data
    except (json.JSONDecodeError, OSError):
        return {"version": VAULT_VERSION, "updated_at": "", "keys": []}


def save_vault(cfg: dict[str, Any], doc: dict[str, Any]) -> None:
    path = vault_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc["version"] = VAULT_VERSION
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    tmp = path.parent / f".key_vault-{uuid.uuid4().hex}.tmp"
    tmp.write_text(json.dumps(doc, indent=2) + "\n")
    tmp.replace(path)


def merge_entries(existing: dict[str, Any], new_rows: list[VaultEntry], cfg: dict[str, Any]) -> dict[str, Any]:
    by_hash: dict[tuple[str, str], dict[str, Any]] = {}
    for row in existing.get("keys") or []:
        h = value_hash(row.get("value") or "")
        by_hash[(row.get("env_var") or "", h)] = row

    for entry in new_rows:
        h = value_hash(entry.value)
        key = (entry.env_var, h)
        if key in by_hash:
            prev = by_hash[key]
            prev["source_host"] = entry.source_host
            prev["source_path"] = entry.source_path
            prev["collected_at"] = entry.collected_at
            continue
        by_hash[key] = entry.to_dict()

    # Enforce max_keys per service
    keys = list(by_hash.values())
    for _sid, svc in (cfg.get("services") or {}).items():
        env_var = svc.get("env_var")
        max_keys = int(svc.get("max_keys") or 99)
        group = [k for k in keys if k.get("env_var") == env_var and k.get("enabled", True)]
        group.sort(key=lambda k: (-int(k.get("priority") or 0), k.get("collected_at") or ""))
        for extra in group[max_keys:]:
            extra["enabled"] = False

    return {"version": VAULT_VERSION, "updated_at": "", "keys": sorted(keys, key=lambda k: (k.get("env_var") or "", -(k.get("priority") or 0)))}


def list_entries(cfg: dict[str, Any] | None = None, *, enabled_only: bool = False) -> list[dict[str, Any]]:
    doc = load_vault(cfg)
    rows = doc.get("keys") or []
    if enabled_only:
        rows = [r for r in rows if r.get("enabled", True)]
    out = []
    for r in rows:
        out.append(
            {
                "id": r.get("id"),
                "env_var": r.get("env_var"),
                "fingerprint": r.get("fingerprint"),
                "source_host": r.get("source_host"),
                "source_path": r.get("source_path"),
                "enabled": r.get("enabled", True),
                "tags": r.get("tags") or [],
                "priority": r.get("priority"),
                "use_count": r.get("use_count") or 0,
            }
        )
    return out


def select_key(
    env_var: str,
    *,
    preset: str | None = None,
    strategy: str | None = None,
    cfg: dict[str, Any] | None = None,
    mark_used: bool = True,
) -> VaultEntry | None:
    cfg = cfg or load_vault_config()
    doc = load_vault(cfg)
    candidates = [VaultEntry.from_dict(r) for r in doc.get("keys") or [] if r.get("env_var") == env_var and r.get("enabled", True)]
    if not candidates:
        return None

    strat = strategy
    if preset and not strat:
        route = (cfg.get("routing") or {}).get(preset) or {}
        prefer = route.get("prefer") or []
        if env_var not in prefer and prefer:
            return None
        strat = route.get("strategy") or "prefer_primary"

    svc = _service_for_var(env_var, cfg)
    strat = strat or (svc.get("strategy") if svc else None) or "prefer_primary"

    if strat == "round_robin":
        candidates.sort(key=lambda c: (c.use_count, -c.priority))
    else:
        candidates.sort(key=lambda c: (-c.priority, c.use_count))

    chosen = candidates[0]
    if mark_used:
        for row in doc.get("keys") or []:
            if row.get("id") == chosen.id:
                row["use_count"] = int(row.get("use_count") or 0) + 1
                row["last_used_at"] = datetime.now(timezone.utc).isoformat()
                break
        save_vault(cfg, doc)
    return chosen


def export_blocked(env_var: str, cfg: dict[str, Any]) -> bool:
    """True when a var must not be written by vault export."""
    perms = cfg.get("permissions") or {}
    if env_var in set(perms.get("deny_vars") or []):
        return True
    if env_var in set(cfg.get("export_deny_vars") or []):
        return True
    for prefix in cfg.get("export_deny_prefixes") or []:
        if env_var.startswith(str(prefix)):
            return True
    return False


def export_env(
    cfg: dict[str, Any] | None = None,
    *,
    target: Path | None = None,
    dry_run: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Write primary + __ALT_N keys to centralized .env."""
    cfg = cfg or load_vault_config()
    doc = load_vault(cfg)
    target = target or ROOT / str(cfg.get("export_target") or ".env")

    by_var: dict[str, list[VaultEntry]] = {}
    for row in doc.get("keys") or []:
        if not row.get("enabled", True):
            continue
        entry = VaultEntry.from_dict(row)
        if export_blocked(entry.env_var, cfg):
            continue
        by_var.setdefault(entry.env_var, []).append(entry)

    updates: dict[str, str] = {}
    for env_var, group in by_var.items():
        group.sort(key=lambda c: (-c.priority, c.use_count))
        updates[env_var] = group[0].value
        for i, alt in enumerate(group[1:], start=1):
            updates[f"{env_var}__ALT_{i}"] = alt.value

    if dry_run:
        return {"target": str(target), "keys": {k: fingerprint(v) for k, v in updates.items()}, "dry_run": True}

    existing = target.read_text().splitlines() if target.exists() else []
    out: list[str] = []
    replaced: set[str] = set()
    for line in existing:
        if "=" not in line or line.strip().startswith("#"):
            out.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if key in updates and (overwrite or not line.split("=", 1)[1].strip()):
            out.append(f"{key}={updates[key]}")
            replaced.add(key)
        elif "__ALT_" not in key:
            out.append(line)
    for key, val in sorted(updates.items()):
        if key not in replaced:
            out.append(f"{key}={val}")

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.parent / f".env-vault-{uuid.uuid4().hex}.tmp"
    tmp.write_text("\n".join(out) + "\n")
    tmp.replace(target)

    return {"target": str(target), "written": len(updates), "dry_run": False}


def set_enabled(entry_id: str, enabled: bool, cfg: dict[str, Any] | None = None) -> bool:
    cfg = cfg or load_vault_config()
    doc = load_vault(cfg)
    found = False
    for row in doc.get("keys") or []:
        if row.get("id") == entry_id:
            row["enabled"] = enabled
            found = True
            break
    if found:
        save_vault(cfg, doc)
    return found


def print_list(cfg: dict[str, Any] | None = None) -> None:
    rows = list_entries(cfg)
    print("==> Key vault (masked)")
    print(f"    {len(rows)} entries")
    for r in rows:
        state = "on" if r.get("enabled", True) else "off"
        tags = ",".join(r.get("tags") or []) or "—"
        print(
            f"  [{state:3}] {r['env_var']:28} {r['fingerprint']:16} "
            f"{r['source_host']:10} {r['source_path']}  tags={tags} id={r['id']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Network key vault — scrape, export, select")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scrape = sub.add_parser("scrape", help="Scrape network hosts into vault")
    p_scrape.add_argument("--collect", action="store_true", help="Collect secret values (policy-gated)")
    p_scrape.add_argument("--host", help="Single host id from config/key_vault.yaml")

    sub.add_parser("list", help="List vault entries (masked)")

    p_export = sub.add_parser("export", help="Export vault → .env")
    p_export.add_argument("--dry-run", action="store_true")
    p_export.add_argument("--target", type=Path)
    p_export.add_argument("--overwrite", action="store_true")

    p_sel = sub.add_parser("select", help="Pick a key for routing")
    p_sel.add_argument("env_var")
    p_sel.add_argument("--preset", help="Routing preset from key_vault.yaml")
    p_sel.add_argument("--strategy", choices=["prefer_primary", "round_robin"])

    p_dis = sub.add_parser("disable", help="Disable vault entry by id")
    p_dis.add_argument("entry_id")

    p_en = sub.add_parser("enable", help="Enable vault entry by id")
    p_en.add_argument("entry_id")

    args = parser.parse_args()
    cfg = load_vault_config()

    if args.cmd == "scrape":
        result = scrape_network(cfg, collect=args.collect, host=args.host)
        print(f"Scraped {result['hosts']} — new {result['new_entries']}, total {result['total_entries']}")
        if not args.collect:
            print("Discovery only (masked). Re-run with --collect to ingest values (see config/key_vault.yaml permissions).")
        return 0

    if args.cmd == "list":
        print_list(cfg)
        return 0

    if args.cmd == "export":
        result = export_env(cfg, target=args.target, dry_run=args.dry_run, overwrite=args.overwrite)
        print(json.dumps({k: v for k, v in result.items() if k != "keys"}, indent=2))
        if args.dry_run and result.get("keys"):
            print("Would write:")
            for k, fp in sorted(result["keys"].items()):
                print(f"  {k}: {fp}")
        return 0

    if args.cmd == "select":
        entry = select_key(args.env_var, preset=args.preset, strategy=args.strategy, cfg=cfg, mark_used=False)
        if not entry:
            print(f"No enabled key for {args.env_var}")
            return 1
        print(json.dumps({"env_var": entry.env_var, "fingerprint": entry.fingerprint, "source_host": entry.source_host, "id": entry.id}))
        return 0

    if args.cmd == "disable":
        ok = set_enabled(args.entry_id, False, cfg)
        print("disabled" if ok else "not found")
        return 0 if ok else 1

    if args.cmd == "enable":
        ok = set_enabled(args.entry_id, True, cfg)
        print("enabled" if ok else "not found")
        return 0 if ok else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

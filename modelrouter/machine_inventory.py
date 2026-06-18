"""
Machine inventory scraper — allowed-folder search for API keys and crypto surfaces.

Security model (wallet-adjacent, read-only audit):
  - Only paths in config/inventory.yaml
  - Secrets are masked; private keys and mnemonics are NEVER printed
  - Keystore files: public address only (from JSON), never ciphertext
  - Presence checks for hot-wallet apps (MetaMask, Ledger Live)

Not a crypto wallet — but similar *inventory* goal: know what credentials exist where.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "inventory.yaml"

OP_REF = re.compile(r"^op://")
ENV_LINE = re.compile(
    r"^(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=\s*(.+)$"
)


@dataclass
class ApiFinding:
    kind: str  # env | pattern | op_ref
    name: str
    path: str
    masked: str
    line: int | None = None


@dataclass
class CryptoFinding:
    surface_id: str
    label: str
    path: str
    status: str  # present | absent | address
    detail: str | None = None


@dataclass
class InventoryReport:
    host: str
    scanned_at: str
    api_findings: list[ApiFinding] = field(default_factory=list)
    crypto_findings: list[CryptoFinding] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "scannedAt": self.scanned_at,
            "stats": self.stats,
            "api": [asdict(f) for f in self.api_findings],
            "crypto": [asdict(f) for f in self.crypto_findings],
        }


def expand(path: str) -> Path:
    return Path(path.replace("~", str(Path.home()))).expanduser()


def load_config(path: Path | None = None) -> dict[str, Any]:
    import yaml

    p = path or DEFAULT_CONFIG
    return yaml.safe_load(p.read_text()) or {}


def mask_value(value: str) -> str:
    value = value.strip().strip("'\"")
    if not value:
        return "(empty)"
    if OP_REF.match(value):
        return value
    if value.startswith("0x") and len(value) >= 10:
        return f"{value[:6]}…{value[-4:]}"
    if len(value) <= 8:
        return "••••••••"
    return f"{value[:4]}…{value[-4:]}"


def _should_skip_dir(name: str, cfg: dict[str, Any]) -> bool:
    return name in set(cfg.get("skip_dir_names") or [])


def _should_skip_file(path: Path, cfg: dict[str, Any]) -> bool:
    suffixes = cfg.get("skip_file_suffixes") or []
    return any(path.name.endswith(s) for s in suffixes)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)


def _scan_env_in_file(
    path: Path,
    api_names: set[str],
    wallet_env: set[str],
    max_bytes: int,
) -> list[ApiFinding]:
    findings: list[ApiFinding] = []
    try:
        if path.stat().st_size > max_bytes:
            return findings
        text = path.read_text(errors="ignore")
    except OSError:
        return findings

    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = ENV_LINE.match(s)
        if m:
            key, val = m.group(1), m.group(2).strip().strip("'\"")
            if key in api_names or key in wallet_env:
                kind = "wallet_env" if key in wallet_env else "env"
                findings.append(
                    ApiFinding(kind, key, _rel(path), mask_value(val), i)
                )
            continue
        if "op://" in s and ":" in s:
            _, val = s.split(":", 1)
            val = val.strip()
            if OP_REF.match(val):
                findings.append(
                    ApiFinding("op_ref", s.split(":")[0].strip(), _rel(path), val, i)
                )
    return findings


def _scan_patterns(path: Path, patterns: list[dict], max_bytes: int) -> list[ApiFinding]:
    findings: list[ApiFinding] = []
    try:
        if path.stat().st_size > max_bytes:
            return findings
        text = path.read_text(errors="ignore")
    except OSError:
        return findings

    for spec in patterns:
        name = spec.get("name", "pattern")
        rx = re.compile(spec["regex"])
        for i, line in enumerate(text.splitlines(), 1):
            for match in rx.finditer(line):
                findings.append(
                    ApiFinding("pattern", name, _rel(path), mask_value(match.group(0)), i)
                )
    return findings


def _iter_scan_files(roots: list[Path], cfg: dict[str, Any]) -> list[Path]:
    globs_env = {".env", ".env.local", ".env.production", ".env.development"}
    names_yaml = {".yaml", ".yml", ".json", ".toml", ".sh", ".zshrc"}
    max_bytes = int(cfg.get("max_file_bytes") or 262144)
    files: list[Path] = []

    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if any(_should_skip_dir(p, cfg) for p in path.parts):
                continue
            if not path.is_file():
                continue
            if _should_skip_file(path, cfg):
                continue
            if path.stat().st_size > max_bytes:
                continue
            if (
                path.name in globs_env
                or path.name.startswith(".env")
                or path.suffix in names_yaml
                or path.name in (".zshrc", ".bashrc", ".bash_profile")
            ):
                files.append(path)
    return sorted(set(files))


def _scan_crypto_surfaces(cfg: dict[str, Any]) -> list[CryptoFinding]:
    findings: list[CryptoFinding] = []
    for surf in cfg.get("crypto_surfaces") or []:
        sid = surf.get("id", "unknown")
        label = surf.get("label", sid)

        if path_s := surf.get("path"):
            p = expand(path_s)
            if p.exists():
                detail = "directory" if p.is_dir() else "file"
                if surf.get("type") == "presence":
                    findings.append(CryptoFinding(sid, label, _rel(p), "present", detail))
                else:
                    findings.append(CryptoFinding(sid, label, _rel(p), "present", detail))
            else:
                findings.append(CryptoFinding(sid, label, _rel(p), "absent", None))
            continue

        if glob_pat := surf.get("glob"):
            roots = [expand(r) for r in surf.get("roots") or ["~/dev"]]
            matched = []
            for root in roots:
                if not root.exists():
                    continue
                matched.extend(root.glob(glob_pat))
            if not matched:
                findings.append(
                    CryptoFinding(sid, label, glob_pat, "absent", "no matches")
                )
                continue
            for p in sorted(matched)[:20]:
                detail = None
                status = "present"
                if surf.get("read_public_address") and (p.suffix == ".json" or "UTC--" in p.name):
                    try:
                        data = json.loads(p.read_text())
                        addr = data.get("address")
                        if addr:
                            status = "address"
                            detail = mask_value(addr if addr.startswith("0x") else f"0x{addr}")
                    except (json.JSONDecodeError, OSError):
                        detail = "keystore (unparsed)"
                elif surf.get("read_json_keys"):
                    try:
                        data = json.loads(p.read_text())
                        parts = [f"{k}={mask_value(str(data[k]))}" for k in surf["read_json_keys"] if k in data]
                        detail = " ".join(parts) if parts else "json present"
                    except (json.JSONDecodeError, OSError):
                        detail = "json (unparsed)"
                elif surf.get("type") == "presence_only":
                    detail = "key material present — not read"
                findings.append(CryptoFinding(sid, label, _rel(p), status, detail))

        for env_name in surf.get("env_names") or []:
            # scanned via main env pass; tag here for wallet warn
            pass

    return findings


def scrape(cfg: dict[str, Any] | None = None) -> InventoryReport:
    import socket

    cfg = cfg or load_config()
    api_names = set(cfg.get("api_key_names") or [])
    wallet_env: set[str] = set()
    for surf in cfg.get("crypto_surfaces") or []:
        wallet_env.update(surf.get("env_names") or [])

    max_bytes = int(cfg.get("max_file_bytes") or 262144)
    patterns = cfg.get("content_patterns") or []

    roots = [expand(r) for r in cfg.get("allowed_roots") or []]
    files: list[Path] = []
    for f in cfg.get("explicit_files") or []:
        p = expand(f)
        if p.is_file():
            files.append(p)
    files.extend(_iter_scan_files(roots, cfg))

    report = InventoryReport(
        host=socket.gethostname(),
        scanned_at=datetime.now(timezone.utc).isoformat(),
    )

    seen: set[tuple[str, str, str]] = set()
    for path in files:
        for finding in _scan_env_in_file(path, api_names, wallet_env, max_bytes):
            sig = (finding.kind, finding.name, finding.path)
            if sig in seen:
                continue
            seen.add(sig)
            report.api_findings.append(finding)
        for finding in _scan_patterns(path, patterns, max_bytes):
            sig = (finding.kind, finding.name, finding.path)
            if sig in seen:
                continue
            seen.add(sig)
            report.api_findings.append(finding)

    report.crypto_findings = _scan_crypto_surfaces(cfg)
    report.stats = {
        "files_scanned": len(files),
        "api_findings": len(report.api_findings),
        "crypto_surfaces": len(report.crypto_findings),
        "wallet_env_hits": sum(1 for f in report.api_findings if f.kind == "wallet_env"),
    }
    return report


def print_report(report: InventoryReport) -> None:
    print(f"==> Machine inventory  {report.host}")
    print(f"    {report.scanned_at}")
    print(f"    files: {report.stats.get('files_scanned', 0)}")
    print()
    print("── API & tokens (masked)")
    for f in sorted(report.api_findings, key=lambda x: (x.name, x.path)):
        warn = " ⚠ wallet" if f.kind == "wallet_env" else ""
        print(f"  {f.name:28} {f.masked:16}  {f.path}{warn}")
    if not report.api_findings:
        print("  (none in allowed paths)")
    print()
    print("── Crypto surfaces")
    for c in report.crypto_findings:
        extra = f"  {c.detail}" if c.detail else ""
        print(f"  [{c.status:7}] {c.label}: {c.path}{extra}")
    print()
    print("Inventory only — not a wallet. Never stores or moves secrets.")


def print_keys_audit(root: Path | None = None, remote_host: str = "kc-mini-lan") -> None:
    """Masked key audit — replaces scripts/discover-keys.sh."""
    import socket
    import subprocess

    root = root or ROOT
    cfg = load_config()
    explicit = [expand(p) for p in (cfg.get("explicit_files") or [])]
    extra = [
        root / ".env",
        root / "secrets.yaml",
        Path.home() / "dev" / "smalshi" / ".env",
        Path.home() / "dev" / "coinbot" / ".env",
        Path.home() / "dev" / "Kalshi_bot" / ".env",
    ]
    paths = []
    seen: set[str] = set()
    for p in explicit + extra:
        rp = str(p.resolve()) if p.exists() else str(p)
        if rp not in seen:
            seen.add(rp)
            paths.append(p)

    print("==> ModelRouter API key audit")
    print(f"    Host: {socket.gethostname()}")
    key_re = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|API_)")

    for path in paths:
        if not path.is_file():
            continue
        print(f"\n── {path}")
        hits = False
        for i, line in enumerate(path.read_text().splitlines(), 1):
            raw = line.strip()
            if raw.startswith("#"):
                continue
            raw = raw.removeprefix("export ").strip()
            if "=" not in raw:
                continue
            k, _, v = raw.partition("=")
            if not key_re.search(k):
                continue
            hits = True
            print(f"  {k:32} {mask_value(v)}")
        if not hits:
            print("  (no key lines)")

    try:
        proc = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=5", remote_host, "true"],
            capture_output=True,
            timeout=6,
        )
        if proc.returncode == 0:
            print(f"\n── {remote_host} (always-on)")
            remote_cmd = (
                'for f in ~/dev/modelrouter/.env ~/dev/smalshi/.env ~/dev/coinbot/.env; do '
                '[ -f "$f" ] || continue; echo "── $f"; '
                'grep -E "^[A-Z_]*(KEY|TOKEN|SECRET|PASSWORD)=" "$f" 2>/dev/null | sed -E "s/=(.*)/=***MASKED***/"; done'
            )
            subprocess.run(["ssh", remote_host, remote_cmd], check=False)
        else:
            print(f"\n── {remote_host}: unreachable (skip remote audit)")
    except (subprocess.TimeoutExpired, OSError):
        print(f"\n── {remote_host}: unreachable (skip remote audit)")

    print("\nFull scan: make inventory")
    print("Vault:     make vault-scrape")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Masked machine inventory scraper")
    parser.add_argument("--json", type=Path, help="Write JSON snapshot path")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--keys-audit",
        action="store_true",
        help="Quick masked key audit (legacy discover-keys)",
    )
    args = parser.parse_args()

    if args.keys_audit:
        print_keys_audit()
        return 0

    cfg = load_config(args.config)
    report = scrape(cfg)
    print_report(report)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report.to_dict(), indent=2) + "\n")
        print(f"Wrote {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

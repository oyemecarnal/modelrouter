#!/usr/bin/env python3
"""Fetch remaining AI API usage from local credentials and write a snapshot JSON."""

from __future__ import annotations

import argparse
import fcntl
import uuid
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SNAPSHOT = Path.home() / "Library/Application Support/TokenWidget/snapshot.json"
DEFAULT_CONFIG = ROOT / "config.json"
LOCAL_CONFIG = ROOT / "config.local.json"
LOCAL_ENV = ROOT / ".env.local"
SESSION_DIR = Path.home() / "Library/Application Support/TokenWidget/sessions"
TIMEOUT = 15

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

AI_KEY_PATTERN = re.compile(
    r"^(OPENAI|ANTHROPIC|CURSOR|GEMINI|GOOGLE|OPENROUTER|GROQ|MISTRAL|COHERE|"
    r"DEEPSEEK|XAI|PERPLEXITY|TOGETHER|FIREWORKS|REPLICATE|HUGGINGFACE|MODELROUTER|"
    r"LITELLM|POLYGON|TELEGRAM|GITHUB|GH|KRAKEN|COINBASE|BINANCE|ALCHEMY|INFURA|"
    r"ETHERSCAN|STRIPE|TWILIO|SENDGRID|DISCORD|SLACK|TAVILY|SERPER|BRAVE_SEARCH|PINECONE|"
    r"WEAVIATE|ELEVENLABS|ASSEMBLYAI|ALPHA_VANTAGE|FINNHUB|KALSHI|POLYMARKET|"
    r"REPLICATE)_"
    r"(API_KEY|API_SECRET|TOKEN|ACCESS_KEY|MASTER_KEY|SALT_KEY|BOT_TOKEN|CDP_KEY_FILE|"
    r"SEARCH_API_KEY|AUTH_TOKEN)=",
    re.I,
)


@dataclass
class UsageWindow:
    label: str
    used_percent: float
    remaining_percent: float | None = None
    reset_at: int | None = None
    detail: str | None = None


@dataclass
class ProviderSnapshot:
    id: str
    name: str
    status: str  # ok | error | unavailable | configured
    plan: str | None = None
    windows: list[UsageWindow] = field(default_factory=list)
    error: str | None = None
    kind: str = "live"  # live | configured


@dataclass
class Snapshot:
    updated_at: int
    providers: list[ProviderSnapshot]
    equity: dict[str, Any] | None = None
    wallets: dict[str, Any] | None = None
    api_catalog: dict[str, Any] | None = None
    api_compare: dict[str, Any] | None = None
    policy_presets: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "updatedAt": self.updated_at,
            "providers": [
                {
                    "id": p.id,
                    "name": p.name,
                    "status": p.status,
                    "kind": p.kind,
                    "plan": p.plan,
                    "windows": [asdict(w) for w in p.windows],
                    "error": p.error,
                }
                for p in self.providers
            ],
        }
        if self.equity is not None:
            out["equity"] = self.equity
        if self.wallets is not None:
            out["wallets"] = self.wallets
        if self.api_catalog is not None:
            out["apiCatalog"] = self.api_catalog
        if self.api_compare is not None:
            out["apiCompare"] = self.api_compare
        if self.policy_presets is not None:
            out["policyPresets"] = self.policy_presets
        return out


def load_config() -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "providers": {
            "openai-codex": True,
            "cursor": True,
            "anthropic": True,
            "gemini": True,
            "openrouter": True,
            "github-copilot": True,
        },
        "show_configured_keys": True,
        "dev_root": str(Path.home() / "dev"),
        "widget_on_top": False,
        "refresh_interval_seconds": 120,
        "session_cache_days": 30,
    }
    for path in (DEFAULT_CONFIG, LOCAL_CONFIG):
        data = read_json(path)
        if isinstance(data, dict):
            cfg.update(data)
            if isinstance(data.get("providers"), dict):
                cfg["providers"] = {**cfg.get("providers", {}), **data["providers"]}
    return cfg


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            val = val.strip().strip("'\"")
            if val:
                values[key] = val
    except Exception:
        pass
    return values


def resolve_secret(name: str, dev_root: Path | None = None) -> str | None:
    val = os.environ.get(name, "").strip()
    if val:
        return val

    cfg = load_config()
    modelrouter_root = Path(cfg.get("modelrouter_root") or (dev_root or Path.home() / "dev") / "modelrouter")
    priority_paths = [
        LOCAL_ENV,
        modelrouter_root / ".env",
        Path.home() / ".openclaw" / ".env",
    ]
    for path in priority_paths:
        v = parse_env_file(path).get(name)
        if v:
            return v

    if dev_root and dev_root.is_dir():
        env_files = set(dev_root.glob("**/.env"))
        env_files.update(dev_root.glob("**/.env.*"))
        for env_path in sorted(env_files):
            if env_path.name.endswith((".example", ".template")):
                continue
            if "node_modules" in env_path.parts or ".venv" in env_path.parts:
                continue
            v = parse_env_file(env_path).get(name)
            if v:
                return v
    return None


def clamp_percent(value: float | int | None) -> float:
    if value is None:
        return 0.0
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(100.0, v))


def http_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    method: str = "GET",
    body: bytes | None = None,
    timeout: int = TIMEOUT,
) -> tuple[int, Any]:
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read())
        except Exception:
            payload = None
        return exc.code, payload


def read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def load_browser_cookies(domain: str) -> dict[str, str]:
    try:
        import browser_cookie3
    except ImportError:
        return {}

    for loader in (
        lambda: browser_cookie3.chrome(domain_name=domain),
        lambda: browser_cookie3.firefox(domain_name=domain),
    ):
        try:
            return {c.name: c.value for c in loader() if c.value}
        except Exception:
            continue
    return {}


def cookie_header(cookies: dict[str, str]) -> str:
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


def save_cookie_session(provider: str, header: str) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSION_DIR / f"{provider}.json"
    path.write_text(
        json.dumps({"cookie": header, "updated_at": int(time.time() * 1000)}, indent=2)
    )


def load_cookie_session(provider: str, max_age_days: int = 30) -> str | None:
    path = SESSION_DIR / f"{provider}.json"
    data = read_json(path)
    if not isinstance(data, dict):
        return None
    cookie = data.get("cookie")
    updated = data.get("updated_at")
    if not isinstance(cookie, str) or not cookie:
        return None
    if isinstance(updated, (int, float)):
        age_ms = time.time() * 1000 - updated
        if age_ms > max_age_days * 86400 * 1000:
            return None
    return cookie


def headers_with_cookie(cookie: str, referer: str) -> dict[str, str]:
    return {**BROWSER_HEADERS, "Cookie": cookie, "Referer": referer}


def claude_browser_headers() -> dict[str, str] | None:
    cookies = load_browser_cookies("claude.ai")
    if not cookies:
        return None
    return headers_with_cookie(cookie_header(cookies), "https://claude.ai/")


def claude_header_candidates(cache_days: int = 30) -> list[tuple[str, dict[str, str]]]:
    candidates: list[tuple[str, dict[str, str]]] = []
    live = claude_browser_headers()
    if live:
        candidates.append(("chrome", live))
    cached = load_cookie_session("claude", cache_days)
    if cached:
        candidates.append(("cache", headers_with_cookie(cached, "https://claude.ai/")))
    return candidates


def fetch_claude_usage(headers: dict[str, str]) -> dict[str, Any] | None:
    status, orgs = http_json("https://claude.ai/api/organizations", headers=headers)
    if status != 200 or not isinstance(orgs, list) or not orgs:
        return None
    org_id = orgs[0].get("uuid")
    if not org_id:
        return None
    status, data = http_json(
        f"https://claude.ai/api/organizations/{org_id}/usage", headers=headers
    )
    if status == 200 and isinstance(data, dict):
        return data
    return None


def cursor_header_candidates(cache_days: int = 30) -> list[tuple[str, dict[str, str]]]:
    candidates: list[tuple[str, dict[str, str]]] = []
    cookies = load_browser_cookies("cursor.com")
    if cookies.get("WorkosCursorSessionToken"):
        candidates.append(
            ("chrome", headers_with_cookie(cookie_header(cookies), "https://cursor.com/"))
        )
    cached = load_cookie_session("cursor", cache_days)
    if cached:
        candidates.append(("cache", headers_with_cookie(cached, "https://cursor.com/")))
    return candidates


def fetch_codex() -> ProviderSnapshot:
    name = "OpenAI Codex"
    token: str | None = None
    account_id: str | None = None

    codex_auth = read_json(Path.home() / ".codex/auth.json")
    if isinstance(codex_auth, dict):
        tokens = codex_auth.get("tokens") or {}
        token = tokens.get("access_token")
        account_id = tokens.get("account_id")

    if not token:
        openclaw = read_json(Path.home() / ".openclaw/agents/main/agent/auth-profiles.json")
        if isinstance(openclaw, dict):
            for profile in (openclaw.get("profiles") or {}).values():
                if profile.get("provider") == "openai-codex" and profile.get("access"):
                    token = profile["access"]
                    account_id = profile.get("accountId")
                    break

    if not token:
        return ProviderSnapshot(
            "openai-codex", name, "unavailable", error="No Codex OAuth token (~/.codex/auth.json)"
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "TokenWidget/1.0",
        "Accept": "application/json",
    }
    if account_id:
        headers["ChatGPT-Account-Id"] = account_id

    status, data = http_json("https://chatgpt.com/backend-api/wham/usage", headers=headers)
    if status != 200 or not isinstance(data, dict):
        return ProviderSnapshot("openai-codex", name, "error", error=f"HTTP {status}")

    windows: list[UsageWindow] = []
    rl = data.get("rate_limit") or {}
    for key, label_fn in (
        ("primary_window", lambda s: f"{max(1, round(s / 3600))}h"),
        ("secondary_window", lambda s: "Week" if s >= 86400 else f"{max(1, round(s / 3600))}h"),
    ):
        win = rl.get(key) or {}
        if "used_percent" in win:
            secs = win.get("limit_window_seconds") or win.get("reset_after_seconds") or 0
            used = clamp_percent(win.get("used_percent"))
            windows.append(
                UsageWindow(
                    label=label_fn(secs),
                    used_percent=used,
                    remaining_percent=clamp_percent(100 - used),
                    reset_at=int(win["reset_at"]) * 1000 if win.get("reset_at") else None,
                )
            )

    plan = data.get("plan_type")
    credits = data.get("credits") or {}
    if credits.get("balance") not in (None, "0", 0):
        plan = f"{plan or 'plan'} (${credits.get('balance')})"

    return ProviderSnapshot("openai-codex", name, "ok", plan=plan, windows=windows)


def fetch_cursor() -> ProviderSnapshot:
    name = "Cursor"
    cfg = load_config()
    cache_days = int(cfg.get("session_cache_days") or 30)

    for source, headers in cursor_header_candidates(cache_days):
        status, data = http_json("https://cursor.com/api/usage-summary", headers=headers)
        if status == 200 and isinstance(data, dict):
            if source == "chrome":
                save_cookie_session("cursor", headers["Cookie"])
            return _cursor_from_usage(data)

    db = Path.home() / "Library/Application Support/Cursor/User/globalStorage/state.vscdb"
    if db.exists():
        conn = sqlite3.connect(str(db))
        row = conn.execute(
            "SELECT value FROM ItemTable WHERE key='cursorAuth/accessToken'"
        ).fetchone()
        conn.close()
        if row and row[0]:
            headers = {
                "Authorization": f"Bearer {row[0]}",
                "User-Agent": "TokenWidget/1.0",
                "Accept": "application/json",
            }
            status, profile = http_json(
                "https://api2.cursor.sh/auth/full_stripe_profile", headers=headers
            )
            if status == 200 and isinstance(profile, dict):
                return ProviderSnapshot(
                    "cursor",
                    name,
                    "ok",
                    plan=profile.get("membershipType"),
                    windows=[
                        UsageWindow(
                            label="Usage",
                            used_percent=0,
                            detail="Log in at cursor.com in Chrome for usage %",
                        )
                    ],
                )

    return ProviderSnapshot(
        "cursor",
        name,
        "unavailable",
        error="Log in at cursor.com in Chrome (cached session expired)",
    )


def _cursor_from_usage(data: dict[str, Any]) -> ProviderSnapshot:
    name = "Cursor"
    windows: list[UsageWindow] = []
    plan_block = ((data.get("individualUsage") or {}).get("plan")) or {}
    total_used = clamp_percent(plan_block.get("totalPercentUsed"))
    if total_used or plan_block.get("limit") is not None:
        remaining_pct = clamp_percent(100 - total_used)
        limit_cents = plan_block.get("limit")
        detail = f"{remaining_pct:.0f}% of included plan left"
        if limit_cents:
            detail += f" (${limit_cents / 100:.0f} cap)"
        windows.append(
            UsageWindow(
                label="Included",
                used_percent=total_used,
                remaining_percent=remaining_pct,
                detail=detail,
            )
        )

    on_demand = ((data.get("individualUsage") or {}).get("onDemand")) or {}
    if on_demand.get("enabled"):
        od_used = clamp_percent(on_demand.get("percentUsed"))
        windows.append(
            UsageWindow(
                label="On-demand",
                used_percent=od_used,
                remaining_percent=clamp_percent(100 - od_used),
            )
        )

    billing_end = data.get("billingCycleEnd")
    reset_at = None
    if billing_end:
        try:
            reset_at = int(
                datetime.fromisoformat(billing_end.replace("Z", "+00:00")).timestamp() * 1000
            )
        except Exception:
            pass
    if reset_at and windows:
        windows[0].reset_at = reset_at

    return ProviderSnapshot(
        "cursor", name, "ok", plan=data.get("membershipType"), windows=windows
    )


def _claude_session_key() -> str:
    for env_key in ("CLAUDE_AI_SESSION_KEY", "CLAUDE_WEB_SESSION_KEY"):
        val = os.environ.get(env_key, "").strip()
        if val:
            return val
    cookie_env = os.environ.get("CLAUDE_WEB_COOKIE", "")
    if "sessionKey=" in cookie_env:
        return cookie_env.split("sessionKey=")[-1].split(";")[0].strip()
    cookies = load_browser_cookies("claude.ai")
    return cookies.get("sessionKey", "")


def fetch_claude() -> ProviderSnapshot:
    cfg = load_config()
    cache_days = int(cfg.get("session_cache_days") or 30)

    for source, headers in claude_header_candidates(cache_days):
        data = fetch_claude_usage(headers)
        if data:
            if source == "chrome":
                save_cookie_session("claude", headers["Cookie"])
            return _claude_from_usage(data)

    session_key = _claude_session_key()
    if not session_key:
        return ProviderSnapshot(
            "anthropic",
            "Claude",
            "unavailable",
            error="Sign in once at claude.ai in Chrome — session will be cached",
        )

    if session_key.startswith("sk-ant-api"):
        oauth_headers = {
            **BROWSER_HEADERS,
            "Authorization": f"Bearer {session_key}",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "oauth-2025-04-20",
        }
        status, data = http_json(
            "https://api.anthropic.com/api/oauth/usage", headers=oauth_headers
        )
        if status == 200 and isinstance(data, dict):
            return _claude_from_usage(data)

    headers = {**BROWSER_HEADERS, "Cookie": f"sessionKey={session_key}", "Referer": "https://claude.ai/"}
    status, orgs = http_json("https://claude.ai/api/organizations", headers=headers)
    if status != 200 or not isinstance(orgs, list) or not orgs:
        return ProviderSnapshot(
            "anthropic",
            "Claude",
            "error",
            error="Session expired — sign in at claude.ai in Chrome once to refresh cache",
        )

    org_id = orgs[0].get("uuid")
    if not org_id:
        return ProviderSnapshot("anthropic", "Claude", "error", error="No organization id")

    status, data = http_json(
        f"https://claude.ai/api/organizations/{org_id}/usage", headers=headers
    )
    if status != 200 or not isinstance(data, dict):
        return ProviderSnapshot("anthropic", "Claude", "error", error=f"HTTP {status}")

    return _claude_from_usage(data)


def _claude_from_usage(data: dict[str, Any]) -> ProviderSnapshot:
    windows: list[UsageWindow] = []
    for key, label in (
        ("five_hour", "5h"),
        ("seven_day", "Week"),
        ("seven_day_sonnet", "Sonnet"),
        ("seven_day_opus", "Opus"),
    ):
        block = data.get(key) or {}
        if block.get("utilization") is None:
            continue
        used = clamp_percent(block["utilization"])
        reset_at = None
        if block.get("resets_at"):
            try:
                reset_at = int(
                    datetime.fromisoformat(block["resets_at"].replace("Z", "+00:00")).timestamp()
                    * 1000
                )
            except Exception:
                pass
        windows.append(
            UsageWindow(
                label=label,
                used_percent=used,
                remaining_percent=clamp_percent(100 - used),
                reset_at=reset_at,
            )
        )

    status = "ok" if windows else "error"
    return ProviderSnapshot(
        "anthropic",
        "Claude",
        status,
        windows=windows,
        error=None if windows else "No usage windows returned",
    )


def _gemini_token() -> str | None:
    candidates = [
        Path.home() / ".gemini/oauth_creds.json",
        Path.home() / ".config/gemini/oauth_creds.json",
        Path.home() / ".local/share/gemini/oauth_creds.json",
    ]
    for path in candidates:
        data = read_json(path)
        if isinstance(data, dict):
            token = data.get("access_token") or data.get("token")
            if isinstance(token, str) and token:
                return token
    return None


def fetch_gemini() -> ProviderSnapshot:
    token = _gemini_token()
    if token:
        status, data = http_json(
            "https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuota",
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            body=b"{}",
        )
        if status == 200 and isinstance(data, dict):
            windows: list[UsageWindow] = []
            pro_min = flash_min = 1.0
            has_pro = has_flash = False
            for bucket in data.get("buckets") or []:
                model = (bucket.get("modelId") or "unknown").lower()
                frac = float(bucket.get("remainingFraction") or 1)
                if "pro" in model:
                    has_pro = True
                    pro_min = min(pro_min, frac)
                if "flash" in model:
                    has_flash = True
                    flash_min = min(flash_min, frac)
            if has_pro:
                used = clamp_percent((1 - pro_min) * 100)
                windows.append(UsageWindow("Pro", used, clamp_percent(100 - used)))
            if has_flash:
                used = clamp_percent((1 - flash_min) * 100)
                windows.append(UsageWindow("Flash", used, clamp_percent(100 - used)))
            if windows:
                return ProviderSnapshot("gemini", "Gemini", "ok", plan="Gemini CLI", windows=windows)

    api_key = resolve_secret("GEMINI_API_KEY") or resolve_secret("GOOGLE_API_KEY")
    if api_key:
        status, _ = http_json(
            "https://generativelanguage.googleapis.com/v1beta/models?key=" + api_key,
            headers={"Accept": "application/json"},
        )
        if status == 200:
            return ProviderSnapshot(
                "gemini",
                "Gemini",
                "ok",
                plan="AI Studio free tier",
                windows=[
                    UsageWindow(
                        label="Flash",
                        used_percent=0,
                        detail="Free: ~1,500 req/day — aistudio.google.com",
                    )
                ],
            )
        return ProviderSnapshot("gemini", "Gemini", "error", error=f"API key invalid (HTTP {status})")

    return ProviderSnapshot(
        "gemini",
        "Gemini",
        "unavailable",
        error="Get free key at aistudio.google.com → GEMINI_API_KEY in .env.local",
    )


def fetch_openrouter() -> ProviderSnapshot:
    api_key = resolve_secret("OPENROUTER_API_KEY")
    if not api_key:
        return ProviderSnapshot(
            "openrouter",
            "OpenRouter",
            "unavailable",
            error="Set OPENROUTER_API_KEY in tokens/.env.local",
        )

    status, data = http_json(
        "https://openrouter.ai/api/v1/credits",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    if status != 200 or not isinstance(data, dict):
        return ProviderSnapshot("openrouter", "OpenRouter", "error", error=f"HTTP {status}")

    payload = data.get("data") if isinstance(data.get("data"), dict) else data
    total = float(payload.get("total_credits") or payload.get("totalCredits") or 0)
    used = float(payload.get("total_usage") or payload.get("totalUsage") or 0)
    remaining = max(0.0, total - used)
    used_pct = clamp_percent((used / total) * 100) if total > 0 else 0.0

    return ProviderSnapshot(
        "openrouter",
        "OpenRouter",
        "ok",
        plan="Credits",
        windows=[
            UsageWindow(
                label="Balance",
                used_percent=used_pct,
                remaining_percent=clamp_percent(100 - used_pct) if total > 0 else None,
                detail=f"${remaining:.2f} left of ${total:.2f}",
            )
        ],
    )


def fetch_copilot() -> ProviderSnapshot:
    github_token = resolve_secret("GITHUB_TOKEN") or resolve_secret("GH_TOKEN")
    if not github_token:
        try:
            import subprocess

            github_token = subprocess.check_output(
                ["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL, timeout=5
            ).strip()
        except Exception:
            github_token = None

    if not github_token:
        code_installed = Path.home() / "Library/Application Support/Code/User/globalStorage/state.vscdb"
        if code_installed.exists():
            return ProviderSnapshot(
                "github-copilot",
                "GitHub Copilot",
                "unavailable",
                error="Run: gh auth login -s copilot",
            )
        return ProviderSnapshot(
            "github-copilot",
            "GitHub Copilot",
            "unavailable",
            error="No GitHub token (gh auth login)",
        )

    status, token_data = http_json(
        "https://api.github.com/copilot_internal/v2/token",
        headers={"Authorization": f"Bearer {github_token}", "Accept": "application/json"},
    )
    if status != 200 or not isinstance(token_data, dict) or not token_data.get("token"):
        return ProviderSnapshot(
            "github-copilot",
            "GitHub Copilot",
            "unavailable",
            error="No Copilot subscription on this GitHub account",
        )

    copilot_token = token_data["token"]
    status, data = http_json(
        "https://api.github.com/copilot_internal/user",
        headers={
            "Authorization": f"token {copilot_token}",
            "Editor-Version": "vscode/1.96.2",
            "User-Agent": "GitHubCopilotChat/0.26.7",
            "X-Github-Api-Version": "2025-04-01",
        },
    )
    if status != 200 or not isinstance(data, dict):
        return ProviderSnapshot("github-copilot", "GitHub Copilot", "error", error=f"HTTP {status}")

    windows: list[UsageWindow] = []
    for label, key in (("Premium", "premium_interactions"), ("Chat", "chat")):
        snap = (data.get("quota_snapshots") or {}).get(key) or {}
        remaining = snap.get("percent_remaining")
        if remaining is not None:
            used = clamp_percent(100 - float(remaining))
            windows.append(
                UsageWindow(label, used, clamp_percent(100 - used))
            )

    return ProviderSnapshot(
        "github-copilot",
        "GitHub Copilot",
        "ok" if windows else "error",
        plan=data.get("copilot_plan"),
        windows=windows,
        error=None if windows else "No quota data",
    )


def fetch_groq(cfg: dict[str, Any] | None = None) -> ProviderSnapshot:
    from key_inventory import fetch_key_provider

    return fetch_key_provider(cfg or load_config(), "GROQ_API_KEY", "Groq", "groq")


def fetch_mistral(cfg: dict[str, Any] | None = None) -> ProviderSnapshot:
    from key_inventory import fetch_key_provider

    return fetch_key_provider(cfg or load_config(), "MISTRAL_API_KEY", "Mistral", "mistral")


LIVE_FETCHERS: dict[str, Callable[[], ProviderSnapshot]] = {
    "openai-codex": fetch_codex,
    "cursor": fetch_cursor,
    "anthropic": fetch_claude,
    "gemini": fetch_gemini,
    "openrouter": fetch_openrouter,
    "github-copilot": fetch_copilot,
    "groq": lambda: fetch_groq(),
    "mistral": lambda: fetch_mistral(),
}


def fetch_all(config: dict[str, Any] | None = None) -> Snapshot:
    cfg = config or load_config()
    enabled = cfg.get("providers") or {}
    providers: list[ProviderSnapshot] = []

    for pid, fn in LIVE_FETCHERS.items():
        if not enabled.get(pid, True):
            continue
        try:
            providers.append(fn())
        except Exception as exc:
            providers.append(ProviderSnapshot(pid, pid, "error", error=str(exc)))

    if cfg.get("show_configured_keys", True):
        from key_inventory import discover_key_cards

        live_by_id = {p.id: p for p in providers}
        skip_key_when_live = {
            "OPENAI_API_KEY": "openai-codex",
            "ANTHROPIC_API_KEY": "anthropic",
            "GEMINI_API_KEY": "gemini",
            "GOOGLE_API_KEY": "gemini",
            "OPENROUTER_API_KEY": "openrouter",
            "GROQ_API_KEY": "groq",
            "MISTRAL_API_KEY": "mistral",
            "CURSOR_API_KEY": "cursor",
            "GITHUB_TOKEN": "github-copilot",
            "GH_TOKEN": "github-copilot",
        }
        for card in discover_key_cards(cfg):
            env_key = card.id.removeprefix("key-").upper().replace("-", "_")
            live_id = skip_key_when_live.get(env_key)
            if live_id:
                live = live_by_id.get(live_id)
                if live and live.status in ("ok", "configured"):
                    continue
            providers.append(card)

    equity: dict[str, Any] | None = None
    if (cfg.get("equity") or {}).get("enabled", True):
        try:
            from fetch_equity import fetch_equity

            equity = fetch_equity(cfg)
        except Exception as exc:
            equity = {"error": str(exc)[:200], "brokers": []}

    wallets: dict[str, Any] | None = None
    if (cfg.get("wallets") or {}).get("enabled", True):
        try:
            from fetch_wallets import fetch_all_wallets

            wallets = fetch_all_wallets(cfg)
        except Exception as exc:
            wallets = {"enabled": True, "wallets": [], "error": str(exc)[:200]}

    api_catalog: dict[str, Any] | None = None
    api_compare: dict[str, Any] | None = None
    if (cfg.get("api_catalog") or {}).get("enabled", True):
        try:
            from api_catalog import catalog_with_status
            from api_comparator import compare_families

            api_catalog = catalog_with_status(cfg)
            api_compare = compare_families(cfg)
        except Exception as exc:
            api_compare = {"error": str(exc)[:200], "families": []}

    policy_presets: dict[str, Any] | None = None
    try:
        from preset_catalog import load_preset_catalog

        policy_presets = load_preset_catalog(cfg)
    except Exception as exc:
        policy_presets = {"error": str(exc)[:200], "presets": [], "projects": []}

    return Snapshot(
        updated_at=int(time.time() * 1000),
        providers=providers,
        equity=equity,
        wallets=wallets,
        api_catalog=api_catalog,
        api_compare=api_compare,
        policy_presets=policy_presets,
    )


def write_snapshot(snapshot: Snapshot, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".snapshot-{uuid.uuid4().hex}.tmp"
    try:
        tmp.write_text(json.dumps(snapshot.to_dict(), indent=2))
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch AI provider usage snapshot")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_SNAPSHOT,
        help=f"Snapshot path (default: {DEFAULT_SNAPSHOT})",
    )
    parser.add_argument("--print", action="store_true", help="Print snapshot to stdout")
    args = parser.parse_args()

    lock_path = DEFAULT_SNAPSHOT.parent / "fetch.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = lock_path.open("w")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0

    try:
        snapshot = fetch_all()
        write_snapshot(snapshot, args.output)

        if args.print:
            print(json.dumps(snapshot.to_dict(), indent=2))

        return 0 if any(p.status == "ok" for p in snapshot.providers if p.kind == "live") else 1
    finally:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()


if __name__ == "__main__":
    sys.exit(main())

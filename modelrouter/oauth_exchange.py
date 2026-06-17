"""OAuth token exchange — Google pilot behind OAUTH_EXCHANGE=1."""

from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = Path.home() / "Library/Application Support/ModelRouter/oauth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
DEFAULT_REDIRECT = "http://127.0.0.1:8766/oauth/callback"


def save_oauth_state(state: str, provider: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / f"{provider}.state"
    path.write_text(state.strip())
    try:
        path.chmod(0o600)
    except OSError:
        pass


def validate_oauth_state(state: str, provider: str) -> bool:
    path = STATE_DIR / f"{provider}.state"
    if not path.exists() or not state:
        return False
    expected = path.read_text().strip()
    try:
        path.unlink()
    except OSError:
        pass
    return secrets.compare_digest(expected, state.strip())


def new_oauth_state(provider: str) -> str:
    state = secrets.token_urlsafe(24)
    save_oauth_state(state, provider)
    return state


def exchange_google_code(
    code: str,
    state: str,
    *,
    redirect_uri: str = DEFAULT_REDIRECT,
    env_path: Path | None = None,
) -> dict[str, Any]:
    """Exchange authorization code; stores refresh token when OAUTH_EXCHANGE=1."""
    if not code:
        return {"ok": False, "error": "missing_code"}
    if not validate_oauth_state(state, "google"):
        return {"ok": False, "error": "invalid_state"}

    if os.environ.get("OAUTH_EXCHANGE") != "1":
        return {"ok": False, "error": "stub", "message": "Set OAUTH_EXCHANGE=1 to exchange tokens"}

    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return {"ok": False, "error": "missing_credentials"}

    body = urllib.parse.urlencode(
        {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode()
    req = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()[:300] if exc.fp else str(exc)
        return {"ok": False, "error": "token_exchange_failed", "detail": detail}
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
        return {"ok": False, "error": "token_exchange_failed", "detail": str(exc)[:200]}

    refresh = (payload.get("refresh_token") or "").strip()
    if not refresh:
        return {"ok": False, "error": "no_refresh_token", "detail": "Google may omit refresh on re-auth"}

    target = env_path or ROOT / ".env"
    from modelrouter.env_store import update_env_file

    update_env_file(target, "GOOGLE_OAUTH_REFRESH_TOKEN", refresh)
    return {"ok": True, "stored": "GOOGLE_OAUTH_REFRESH_TOKEN", "env_path": str(target)}

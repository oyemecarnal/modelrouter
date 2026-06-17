#!/usr/bin/env python3
"""Native desktop panel for AI API token usage."""

from __future__ import annotations

import faulthandler
import json
import signal
import uuid
import subprocess
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from log_util import install_excepthook, log_event, setup_logging

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
WIDGET_DIR = Path(__file__).resolve().parent
SUPPORT = Path.home() / "Library/Application Support/TokenWidget"
SNAPSHOT = SUPPORT / "snapshot.json"
WIDGET_TOKEN_PATH = SUPPORT / "widget_token"
FETCHER = SCRIPTS / "fetch_usage.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
VENV_PYTHON = ROOT / ".venv" / "bin" / "python3"
LOCAL_ENV = ROOT / ".env.local"
ENV_EXAMPLE = ROOT / ".env.local.example"
PORT = 8765

logger = setup_logging()
install_excepthook(logger)
faulthandler.enable()


def widget_token() -> str:
    SUPPORT.mkdir(parents=True, exist_ok=True)
    if WIDGET_TOKEN_PATH.exists():
        return WIDGET_TOKEN_PATH.read_text().strip()
    token = uuid.uuid4().hex
    WIDGET_TOKEN_PATH.write_text(token)
    try:
        WIDGET_TOKEN_PATH.chmod(0o600)
    except OSError:
        pass
    return token


def load_widget_config() -> dict:
    cfg: dict = {
        "app_name": "ModelRouter Keys",
        "widget_on_top": False,
        "widget_size": 420,
        "refresh_interval_seconds": 120,
        "widget_fetch_in_panel": True,
        "edit_file": ".env.local",
    }
    for path in (ROOT / "config.json", ROOT / "config.local.json"):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text())
            if isinstance(data, dict):
                cfg.update(data)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("config read failed %s: %s", path, exc)
    return cfg


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def do_GET(self) -> None:
        try:
            if self.path.startswith("/snapshot.json"):
                payload = SNAPSHOT.read_text() if SNAPSHOT.exists() else '{"providers":[]}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(payload.encode())
                return

            if self.path.startswith("/meta.json"):
                cfg = load_widget_config()
                meta = json.dumps(
                    {
                        "appName": cfg.get("app_name", "ModelRouter Keys"),
                        "editFile": str(ROOT / cfg.get("edit_file", ".env.local")),
                        "widgetToken": Handler.widget_token,
                    }
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(meta.encode())
                return

            if self.path.startswith("/wallet-txs"):
                payload = wallet_transactions_response(self.path)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode())
                return

            path = WIDGET_DIR / "index.html"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(path.read_bytes())
        except Exception:
            logger.exception("HTTP GET failed path=%s", self.path)
            log_event("http_error", path=self.path, error=traceback.format_exc())
            raise

    def do_POST(self) -> None:
        if not _authorized(self):
            self.send_response(403)
            self.end_headers()
            return
        if self.path == "/refresh":
            if Handler.panel_fetch_enabled:
                run_fetch(reason="ui_refresh")
            self.send_response(204)
            self.end_headers()
            return
        if self.path == "/edit":
            open_edit_file()
            self.send_response(204)
            self.end_headers()
            return
        if self.path == "/wallets/add":
            status, body = wallet_add_response(self)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())
            return
        if self.path == "/wallets/remove":
            status, body = wallet_remove_response(self)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())
            return
        if self.path == "/keys/add":
            status, body = key_add_response(self)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())
            return
        if self.path == "/connectors/paste":
            status, body = connector_paste_response(self)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())
            return
        if self.path == "/vault/toggle":
            status, body = vault_toggle_response(self)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())
            return
        if self.path == "/api-assess":
            status, body = api_assess_response()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())
            return
        self.send_response(404)
        self.end_headers()

    panel_fetch_enabled = False
    widget_token: str = ""


def _authorized(handler: BaseHTTPRequestHandler) -> bool:
    return handler.headers.get("X-Widget-Token") == Handler.widget_token


def _read_post_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        data = json.loads(raw.decode())
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def wallet_add_response(handler: BaseHTTPRequestHandler) -> tuple[int, dict]:
    try:
        from wallet_store import add_wallet

        body = _read_post_json(handler)
        entry = add_wallet(
            label=str(body.get("label") or ""),
            chain=str(body.get("chain") or "ethereum"),
            address=str(body.get("address") or ""),
            kind=str(body.get("kind") or "cold"),
        )
        run_fetch(reason="wallet_added")
        return 200, {"ok": True, "wallet": entry}
    except ValueError as exc:
        return 400, {"ok": False, "error": str(exc)}
    except Exception as exc:
        logger.exception("wallet add failed")
        return 500, {"ok": False, "error": str(exc)}


def wallet_remove_response(handler: BaseHTTPRequestHandler) -> tuple[int, dict]:
    try:
        from wallet_store import remove_wallet

        body = _read_post_json(handler)
        wallet_id = str(body.get("id") or "")
        if not wallet_id:
            return 400, {"ok": False, "error": "id required"}
        if not remove_wallet(wallet_id):
            return 404, {"ok": False, "error": "not found"}
        run_fetch(reason="wallet_removed")
        return 200, {"ok": True}
    except Exception as exc:
        logger.exception("wallet remove failed")
        return 500, {"ok": False, "error": str(exc)}


def key_add_response(handler: BaseHTTPRequestHandler) -> tuple[int, dict]:
    try:
        from key_store import add_key

        body = _read_post_json(handler)
        env_name = str(body.get("env") or "")
        value = str(body.get("value") or "")
        add_key(env_name, value)
        run_fetch(reason="key_added")
        return 200, {"ok": True, "env": env_name.upper()}
    except ValueError as exc:
        return 400, {"ok": False, "error": str(exc)}
    except Exception as exc:
        logger.exception("key add failed")
        return 500, {"ok": False, "error": str(exc)}


def connector_paste_response(handler: BaseHTTPRequestHandler) -> tuple[int, dict]:
    try:
        from connector_paste import paste_connector
        from fetch_usage import load_config

        body = _read_post_json(handler)
        provider = str(body.get("provider") or "").strip()
        value = str(body.get("value") or "")
        if not provider:
            return 400, {"ok": False, "error": "provider required"}
        cfg = load_widget_config()
        cfg.update(load_config())
        push = body.get("push", True) is not False
        restart = body.get("restart", True) is not False
        result = paste_connector(cfg, provider, value, push=push, restart=restart)
        run_fetch(reason="connector_pasted")
        return 200, {"ok": True, **result}
    except ValueError as exc:
        return 400, {"ok": False, "error": str(exc)}
    except Exception as exc:
        logger.exception("connector paste failed")
        return 500, {"ok": False, "error": str(exc)}


def vault_toggle_response(handler: BaseHTTPRequestHandler) -> tuple[int, dict]:
    try:
        import sys
        from pathlib import Path

        from fetch_usage import load_config

        body = _read_post_json(handler)
        entry_id = str(body.get("id") or "").strip()
        if not entry_id:
            return 400, {"ok": False, "error": "id required"}
        enabled = body.get("enabled")
        if enabled is None:
            return 400, {"ok": False, "error": "enabled required"}

        cfg = load_widget_config()
        cfg.update(load_config())
        root = Path(cfg.get("modelrouter_root") or Path.home() / "dev" / "modelrouter")
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from modelrouter.key_vault import set_enabled

        if not set_enabled(entry_id, bool(enabled)):
            return 404, {"ok": False, "error": "not found"}
        run_fetch(reason="vault_toggled")
        return 200, {"ok": True, "id": entry_id, "enabled": bool(enabled)}
    except Exception as exc:
        logger.exception("vault toggle failed")
        return 500, {"ok": False, "error": str(exc)}


def api_assess_response() -> tuple[int, dict]:
    try:
        from api_assess import assess_apis, build_assessment_payload, rule_based_summary
        from fetch_usage import load_config

        cfg = load_widget_config()
        cfg.update(load_config())
        result = assess_apis(cfg, use_llm=True)
        narrative = result.get("narrative") or {}
        if narrative.get("status") != "ok" or not narrative.get("text"):
            payload = build_assessment_payload(cfg)
            narrative = {
                "status": "offline",
                "text": rule_based_summary(payload),
                "error": narrative.get("error"),
            }
            result["narrative"] = narrative
        return 200, {"ok": True, "assessment": result}
    except Exception as exc:
        logger.exception("api assess failed")
        return 500, {"ok": False, "error": str(exc)}


def wallet_transactions_response(path: str) -> dict:
    try:
        from fetch_usage import load_config
        from fetch_wallets import fetch_wallet_transactions

        query = path.split("?", 1)
        params: dict[str, str] = {}
        if len(query) > 1:
            for part in query[1].split("&"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    params[k] = v
        wallet_id = params.get("id", "")
        if not wallet_id:
            return {"error": "id required", "transactions": []}
        return fetch_wallet_transactions(wallet_id, load_config())
    except Exception as exc:
        logger.exception("wallet txs failed")
        return {"error": str(exc), "transactions": []}


def edit_file_path() -> Path:
    cfg = load_widget_config()
    rel = cfg.get("edit_file", ".env.local")
    return ROOT / rel if not Path(rel).is_absolute() else Path(rel)


def open_edit_file() -> None:
    path = edit_file_path()
    if not path.exists():
        if ENV_EXAMPLE.exists():
            path.write_text(ENV_EXAMPLE.read_text())
        else:
            path.write_text("# API keys for ModelRouter Keys widget\n")
    try:
        subprocess.run(["open", "-e", str(path)], check=False)
    except Exception:
        logger.exception("failed to open edit file %s", path)


def _fetch_python() -> Path:
    """Prefer modelrouter .venv (working SSL) over tokens/.venv."""
    try:
        from fetch_usage import load_config

        cfg = load_widget_config()
        cfg.update(load_config())
        mr_root = Path(cfg.get("modelrouter_root") or (ROOT.parent.parent))
        mr_python = mr_root / ".venv" / "bin" / "python3"
        if mr_python.exists():
            return mr_python
    except Exception:
        pass
    if VENV_PYTHON.exists():
        return VENV_PYTHON
    return Path(sys.executable)


def run_fetch(reason: str = "manual") -> None:
    python = str(_fetch_python())
    try:
        result = subprocess.run(
            [python, str(FETCHER)],
            check=False,
            timeout=150,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            log_event("fetch_ok", reason=reason)
            logger.debug("fetch ok reason=%s", reason)
        else:
            log_event(
                "fetch_fail",
                reason=reason,
                exit_code=result.returncode,
                stderr=(result.stderr or "")[-500:],
            )
            logger.warning("fetch failed reason=%s code=%s", reason, result.returncode)
    except Exception as exc:
        log_event("fetch_fail", reason=reason, error=str(exc))
        logger.exception("fetch exception reason=%s", reason)


def start_server() -> ThreadingHTTPServer:
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError as exc:
        log_event("port_bind_fail", port=PORT, error=str(exc))
        logger.error("cannot bind port %s: %s", PORT, exc)
        raise
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log_event("http_server_start", port=PORT)
    return server


def start_fetch_loop(interval_seconds: int) -> None:
    def loop() -> None:
        while True:
            time.sleep(interval_seconds)
            run_fetch(reason="background_loop")

    threading.Thread(target=loop, name="fetch-loop", daemon=True).start()


def start_heartbeat() -> None:
    def loop() -> None:
        while True:
            time.sleep(300)
            log_event("heartbeat")
            logger.debug("heartbeat")

    threading.Thread(target=loop, name="heartbeat", daemon=True).start()


def install_signal_handlers() -> None:
    def stop(reason: str, signum: int, _frame) -> None:
        log_event("widget_signal", signal=signum, reason=reason)
        logger.info("received signal %s (%s)", signum, reason)
        raise SystemExit(0)

    for sig, name in ((signal.SIGTERM, "SIGTERM"), (signal.SIGINT, "SIGINT")):
        signal.signal(sig, lambda s, f, n=name: stop(n, s, f))


def main() -> None:
    import webview

    install_signal_handlers()
    log_event("widget_start", pid=__import__("os").getpid())
    logger.info("widget starting")

    Handler.widget_token = widget_token()
    cfg = load_widget_config()
    refresh_s = int(cfg.get("refresh_interval_seconds") or 120)
    on_top = bool(cfg.get("widget_on_top", False))
    panel_fetch = bool(cfg.get("widget_fetch_in_panel", False))
    Handler.panel_fetch_enabled = panel_fetch

    if panel_fetch and not SNAPSHOT.exists():
        run_fetch(reason="startup")

    server = start_server()
    if panel_fetch:
        start_fetch_loop(refresh_s)
    start_heartbeat()
    url = f"http://127.0.0.1:{PORT}/"

    size = int(cfg.get("widget_size") or 420)
    title = str(cfg.get("app_name") or "ModelRouter Keys")

    window = webview.create_window(
        title,
        url,
        width=size,
        height=size,
        x=80,
        y=80,
        resizable=True,
        on_top=on_top,
        min_size=(320, 320),
    )

    def on_loaded() -> None:
        def focus_window() -> None:
            time.sleep(0.4)
            try:
                window.show()
                window.restore()
            except Exception:
                logger.debug("window show/restore skipped", exc_info=True)
            try:
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to set frontmost of '
                        'the first process whose unix id is '
                        f"{__import__('os').getpid()} to true",
                    ],
                    check=False,
                    capture_output=True,
                )
            except Exception:
                logger.debug("window focus skipped", exc_info=True)

        threading.Thread(target=focus_window, name="focus-window", daemon=True).start()
        if panel_fetch:
            run_fetch(reason="window_loaded")

    try:
        logger.info(
            "webview starting on_top=%s panel_fetch=%s (launchd handles fetch=%s)",
            on_top,
            panel_fetch,
            not panel_fetch,
        )
        webview.start(on_loaded, debug=False, gui="cocoa")
        log_event("widget_stop", reason="window_closed")
        logger.info("webview exited normally (window closed)")
    except Exception:
        log_event("widget_stop", reason="exception")
        logger.exception("webview crashed")
        raise
    finally:
        server.shutdown()
        log_event("widget_shutdown")
        logger.info("widget shutdown complete")


if __name__ == "__main__":
    main()

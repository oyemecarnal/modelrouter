#!/usr/bin/env python3
"""Native desktop panel for AI API token usage."""

from __future__ import annotations

import faulthandler
import json
import signal
import subprocess
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from log_util import install_excepthook, log_event, setup_logging

ROOT = Path(__file__).resolve().parent.parent
WIDGET_DIR = Path(__file__).resolve().parent
SNAPSHOT = Path.home() / "Library/Application Support/TokenWidget/snapshot.json"
FETCHER = ROOT / "scripts" / "fetch_usage.py"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python3"
LOCAL_ENV = ROOT / ".env.local"
ENV_EXAMPLE = ROOT / ".env.local.example"
PORT = 8765

logger = setup_logging()
install_excepthook(logger)
faulthandler.enable()


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
                    }
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(meta.encode())
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
        self.send_response(404)
        self.end_headers()

    panel_fetch_enabled = False


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


def run_fetch(reason: str = "manual") -> None:
    python = str(VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable))
    try:
        result = subprocess.run(
            [python, str(FETCHER)],
            check=False,
            timeout=90,
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

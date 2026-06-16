#!/usr/bin/env python3
"""Dev-only OAuth callback listener — logs code receipt, does not exchange tokens."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

PORT = 8766
ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/oauth/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")
            return
        params = parse_qs(parsed.query)
        code = (params.get("code") or [""])[0]
        state = (params.get("state") or [""])[0]
        err = (params.get("error") or [""])[0]
        body = {
            "status": "stub",
            "message": "Callback received — token exchange not implemented (Phase 3)",
            "has_code": bool(code),
            "has_state": bool(state),
            "error": err or None,
            "spec": "docs/OAUTH_CONNECTOR_SPEC.md",
            "paste_key": "make connect-google",
        }
        print(json.dumps(body, indent=2), file=sys.stderr)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())


def main() -> None:
    print(f"OAuth callback stub on http://127.0.0.1:{PORT}/oauth/callback", file=sys.stderr)
    print("Press Ctrl+C to stop. Spec: docs/OAUTH_CONNECTOR_SPEC.md", file=sys.stderr)
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Verify generated gateway configs match policy_presets SSOT."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_gateway_config.py"), "--check"],
        cwd=ROOT,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())

"""Logging helpers for TokenWidget diagnostics."""

from __future__ import annotations

import json
import logging
import sys
import time
import traceback
from pathlib import Path

SUPPORT = Path.home() / "Library/Application Support/TokenWidget"
EVENTS = SUPPORT / "widget_events.jsonl"
LOG_FILE = SUPPORT / "widget.log"


def setup_logging() -> logging.Logger:
    SUPPORT.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("tokenwidget")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    stream = logging.StreamHandler(sys.stderr)
    stream.setLevel(logging.INFO)
    stream.setFormatter(fmt)
    logger.addHandler(stream)
    return logger


def log_event(event: str, **fields) -> None:
    SUPPORT.mkdir(parents=True, exist_ok=True)
    record = {"ts": int(time.time() * 1000), "event": event, **fields}
    with EVENTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def install_excepthook(logger: logging.Logger) -> None:
    def hook(exc_type, exc, tb):
        logger.critical("uncaught exception", exc_info=(exc_type, exc, tb))
        log_event("crash", error=str(exc), traceback="".join(traceback.format_exception(exc_type, exc, tb)))
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = hook

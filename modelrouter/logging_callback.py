"""
Structured JSON logging callback for LiteLLM proxy.
Registered in config/modelrouter.yaml as modelrouter.logging_callback
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Optional

from litellm.integrations.custom_logger import CustomLogger


class ModelRouterLogger(CustomLogger):
    def log_pre_api_call(self, model: str, messages: list, kwargs: dict) -> None:
        request_id = kwargs.get("litellm_call_id", "unknown")
        metadata = kwargs.get("metadata") or {}
        project = metadata.get("user") or metadata.get("project") or metadata.get("trace_user")
        print(
            json.dumps(
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "event": "request_start",
                    "request_id": request_id,
                    "model": model,
                    "project": project,
                    "stream": kwargs.get("stream", False),
                }
            ),
            flush=True,
        )

    async def async_log_success_event(
        self,
        kwargs: dict,
        response_obj: Any,
        start_time: float,
        end_time: float,
    ) -> None:
        duration_ms = round((end_time - start_time) * 1000, 1)
        usage = getattr(response_obj, "usage", None)
        print(
            json.dumps(
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "event": "request_success",
                    "request_id": kwargs.get("litellm_call_id"),
                    "model": kwargs.get("model"),
                    "duration_ms": duration_ms,
                    "tokens": getattr(usage, "total_tokens", None) if usage else None,
                }
            ),
            flush=True,
        )

    async def async_log_failure_event(
        self,
        kwargs: dict,
        response_obj: Any,
        start_time: float,
        end_time: float,
    ) -> None:
        duration_ms = round((end_time - start_time) * 1000, 1)
        print(
            json.dumps(
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "event": "request_failure",
                    "request_id": kwargs.get("litellm_call_id"),
                    "model": kwargs.get("model"),
                    "duration_ms": duration_ms,
                    "error": str(response_obj),
                }
            ),
            flush=True,
        )


# LiteLLM discovers this instance by module path
logging_callback = ModelRouterLogger()

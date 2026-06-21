from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Iterator

from .logging_setup import redact

logger = logging.getLogger("dip_poc.audit")


def _emit(event_type: str, level: int = logging.INFO, **fields: Any) -> None:
    safe = {k: (redact(v) if isinstance(v, str) else v) for k, v in fields.items()}
    logger.log(level, "%s", event_type, extra={"event": {"type": event_type, **safe}})


# tool-call audit
def tool_selected(tool_name: str, args: dict) -> None:
    """LLM autonomously chose a tool. THE key bonus-task observability event."""
    _emit("tool.selected", tool=tool_name, args=_safe_args(args))


def tool_completed(tool_name: str, duration_ms: float, ok: bool, error: str | None = None) -> None:
    _emit(
        "tool.completed",
        level=logging.INFO if ok else logging.ERROR,
        tool=tool_name,
        duration_ms=round(duration_ms, 1),
        status="ok" if ok else "error",
        error=error,
    )


# API-call audit
def api_request(endpoint: str, params: dict, cache_hit: bool) -> None:
    _emit("api.request", endpoint=endpoint, params=_safe_args(params), cache_hit=cache_hit)


def api_response(endpoint: str, status: int, duration_ms: float, attempt: int) -> None:
    _emit(
        "api.response",
        level=logging.INFO if status < 400 else logging.WARNING,
        endpoint=endpoint,
        status=status,
        duration_ms=round(duration_ms, 1),
        attempt=attempt,
    )


def api_retry(endpoint: str, attempt: int, reason: str, backoff_s: float) -> None:
    _emit("api.retry", level=logging.WARNING, endpoint=endpoint,
          attempt=attempt, reason=reason, backoff_s=backoff_s)


# security audit
def security_auth_source(service: str, source: str) -> None:
    """Record WHERE a credential came from (env vs. baked-in fallback)."""
    _emit("security.auth_source", service=service, source=source)


def security_validation_rejected(tool_name: str, reason: str) -> None:
    _emit("security.validation_rejected", level=logging.WARNING,
          tool=tool_name, reason=reason)


# timing helper
@contextmanager
def timed(event_label: str) -> Iterator[dict]:
    """Context manager that measures wall-time and exposes it via a dict."""
    box: dict = {"duration_ms": 0.0}
    start = time.perf_counter()
    try:
        yield box
    finally:
        box["duration_ms"] = (time.perf_counter() - start) * 1000.0


def _safe_args(args: dict) -> dict:
    """Never let raw secret-bearing params land in an event verbatim."""
    out = {}
    for k, v in args.items():
        if k.lower() in {"apikey", "api_key", "authorization", "key", "token"}:
            out[k] = "***REDACTED***"
        else:
            out[k] = v
    return out

from __future__ import annotations

import contextvars
import json
import logging
import re
import sys
import time
import uuid

# Correlation ID is a short random string that ties together all log lines of one request.
correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default="-"
)


def new_correlation_id() -> str:
    cid = uuid.uuid4().hex[:12]
    correlation_id.set(cid)
    return cid

# nothing regarding api keys and auth should appear in logs
_REDACTION_PATTERNS = [
    (re.compile(r"(apikey=)[^&\s]+", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"(ApiKey\s+)[^\s\"']+"), r"\1***REDACTED***"),
    (re.compile(r"(Authorization[\"']?\s*[:=]\s*[\"']?)[^\s\"',}]+", re.IGNORECASE),
     r"\1***REDACTED***"),
    (re.compile(r"\bgsk_[A-Za-z0-9]{8,}\b"), "***REDACTED_GROQ_KEY***"),
    (re.compile(r"\b[A-Za-z0-9]{6,8}\.[A-Za-z0-9]{20,}\b"), "***REDACTED_DIP_KEY***"),
]


def redact(text: str) -> str:
    if not text:
        return text
    for pattern, repl in _REDACTION_PATTERNS:
        text = pattern.sub(repl, text)
    return text


class RedactionFilter(logging.Filter):
    """Last line of defence: scrub any secret that slipped into a message."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        if record.args:
            record.args = tuple(
                redact(a) if isinstance(a, str) else a for a in record.args
            )
        return True


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per line, enriched with correlation id + extras."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "correlation_id": correlation_id.get(),
            "msg": record.getMessage(),
        }
        # Structured extras passed via logger.info(..., extra={"event": {...}})
        if hasattr(record, "event"):
            payload["event"] = record.event  # type: ignore[attr-defined]
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return redact(json.dumps(payload, ensure_ascii=False))


_CONFIGURED = False


def configure_logging(level: int = logging.INFO, json_output: bool = True) -> None:
    """Idempotent root-logger setup. Call once at each entry point."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stderr)
    if json_output:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(levelname)s [%(name)s] %(message)s")
        )
    handler.addFilter(RedactionFilter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    _CONFIGURED = True

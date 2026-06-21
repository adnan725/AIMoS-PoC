"""Observability for the DIP PoC: structured logging, audit events, security.

Three levels, deliberately separated:

  1. Logging  (logging_setup.py) — JSON lines, correlation ids, secret
     redaction. The transport.
  2. Audit    (audit.py)         — typed events: tool.selected, api.request,
     security.auth_source, … The semantics.
  3. Validation (validation.py)  — input guards on tool arguments before they
     reach the API. The security gate.

Production migration: every audit.* function is the seam where you'd also emit
an OpenTelemetry span/metric. Because callers only touch these helpers (never
the logging internals), adding OTel is a change in this package alone — the
business logic stays untouched.
"""
from .audit import (
    api_request,
    api_response,
    api_retry,
    security_auth_source,
    security_validation_rejected,
    timed,
    tool_completed,
    tool_selected,
)
from .logging_setup import configure_logging, new_correlation_id, redact
from .validation import ValidationError, validate_tool_args

__all__ = [
    "configure_logging",
    "new_correlation_id",
    "redact",
    "tool_selected",
    "tool_completed",
    "api_request",
    "api_response",
    "api_retry",
    "security_auth_source",
    "security_validation_rejected",
    "timed",
    "validate_tool_args",
    "ValidationError",
]

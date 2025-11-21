# backend/app/logging_config.py

import logging
import json
import contextvars
from typing import Optional
from datetime import datetime

# Context variables
_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
_consent_trace_var: contextvars.ContextVar[str] = contextvars.ContextVar("consent_trace_id", default="")

def set_request_id(value: Optional[str]) -> None:
    _request_id_var.set(value or "")

def get_request_id() -> str:
    return _request_id_var.get() or ""

def set_consent_trace_id(value: Optional[str]) -> None:
    _consent_trace_var.set(value or "")

def get_consent_trace_id() -> str:
    return _consent_trace_var.get() or ""

def clear_trace_context() -> None:
    _request_id_var.set("")
    _consent_trace_var.set("")

class JsonMessageAdapter(logging.LoggerAdapter):
    """
    LoggerAdapter that converts the message into a JSON string stored in rec.msg.
    This avoids passing arbitrary kwargs into Logger._log and matches the tests'
    expectation that json.loads(rec.msg) works.
    """

    def process(self, msg, kwargs):
        # Build basic JSON payload
        payload = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": logging.getLevelName(kwargs.get("levelno", logging.INFO)),
            "logger": self.logger.name,
            "message": msg if isinstance(msg, str) else str(msg),
            "request_id": get_request_id(),
            "consent_trace_id": get_consent_trace_id(),
        }

        # If caller provided structured extra via kwargs['extra'] and it contains a dict
        extra = kwargs.pop("extra", {}) or {}
        # Support callers passing extra={"extra_fields": {...}} or extra={"foo":"bar"}
        # Merge additional keys without overwriting core keys
        if isinstance(extra, dict):
            extra_fields = extra.get("extra_fields", extra)
            if isinstance(extra_fields, dict):
                for k, v in extra_fields.items():
                    if k not in payload:
                        payload[k] = v
            else:
                # if someone passed extra as plain keys, merge them too
                for k, v in extra.items():
                    if k not in payload:
                        payload[k] = v

        # Return JSON string as the message
        return (json.dumps(payload), kwargs)


def configure_logging(level: int = logging.INFO, force: bool = False) -> None:
    """
    Configure logging in a test-friendly way.
    - If force=False, do not clear existing handlers (pytest's caplog can attach).
    - If no handlers exist, add a StreamHandler that writes the adapter's msg.
    """
    root = logging.getLogger()
    root.setLevel(level)

    if force:
        root.handlers.clear()

    if not root.handlers:
        h = logging.StreamHandler()
        # We expect the adapter to produce JSON in record.msg
        h.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(h)


def get_logger(name: str) -> logging.LoggerAdapter:
    base = logging.getLogger(name)
    return JsonMessageAdapter(base, {})

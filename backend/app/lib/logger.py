# backend/app/lib/logger.py
"""
Shared structured JSON logger helper.

- Uses contextvars to attach request_id and consent_trace_id to every log record.
- Produces compact JSON per log line.
- Does NOT log any PHI (be careful to never pass PHI into logging args).
"""

from __future__ import annotations
import logging
import json
import time
from typing import Any, Dict
from contextvars import ContextVar

# Context variables to carry trace identifiers across request lifecycle
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
consent_trace_id_var: ContextVar[str | None] = ContextVar("consent_trace_id", default=None)

class JsonFormatter(logging.Formatter):
    """A simple JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        # Base record information
        base: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
        }

        # Attach trace ids if available (without enforcing presence)
        req_id = request_id_var.get()
        if req_id:
            base["request_id"] = req_id

        cons_id = consent_trace_id_var.get()
        if cons_id:
            base["consent_trace_id"] = cons_id

        # Include any structured fields passed using record.__dict__['extra'] or via kwargs
        # Avoid logging sensitive fields - we expect callers to respect no-PHI rule.
        # Collect any non-standard attributes
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in ('name','msg','args','levelname','levelno','pathname','filename','module',
                         'exc_info','exc_text','stack_info','lineno','funcName','created',
                         'msecs','relativeCreated','thread','threadName','processName','process')
        }

        if extras:
            base["extra"] = extras

        return json.dumps(base, default=str, separators=(",", ":"))

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a configured JSON logger.
    - Idempotent: repeated calls return the same logger object and handlers are guarded.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # Default to INFO (change via env/config in real deployments)
        logger.setLevel(logging.INFO)
        # Prevent double logging when used within libraries/apps
        logger.propagate = False

    return logger

def set_request_id(request_id: str | None) -> None:
    """Set the request_id in contextvar for downstream logging."""
    request_id_var.set(request_id)

def set_consent_trace_id(consent_trace_id: str | None) -> None:
    """Set the consent_trace_id in contextvar for downstream logging."""
    consent_trace_id_var.set(consent_trace_id)

def clear_trace_context() -> None:
    """Clear trace context vars (useful in tests)."""
    request_id_var.set(None)
    consent_trace_id_var.set(None)

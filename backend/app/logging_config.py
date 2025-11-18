import logging
import sys
import json
import time
import uuid
from typing import Any, Dict

# ==========================================================
#  🔐 LOG MASKING UTILITIES (NO PHI, NO RAW IDENTIFIERS)
# ==========================================================

SENSITIVE_KEYS = {"password", "token", "abha_number", "email", "phone", "otp"}

def mask_value(key: str, value: Any) -> Any:
    """Mask sensitive fields according to zero-trust policy."""
    if key.lower() in SENSITIVE_KEYS and isinstance(value, str):
        if "@" in value:
            # mask email
            name, domain = value.split("@")
            return f"{name[0]}***@{domain}"
        return "***MASKED***"
    return value


def mask_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive fields in dictionaries."""
    return {k: mask_value(k, v) for k, v in data.items()}


# ==========================================================
#  🧱 STRUCTURED JSON FORMATTER
# ==========================================================

class JsonLogFormatter(logging.Formatter):
    """Structured JSON log formatter for global application logging."""

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": int(time.time() * 1000),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", record.msg),
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", None),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Attach extra fields and apply masking
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log["extra"] = mask_dict(record.extra_data)

        return json.dumps(log)


# ==========================================================
#  🔄 TRACE ID SUPPORT (GLOBAL UTILITY)
# ==========================================================

def get_trace_id() -> str:
    """Return a new UUID4 trace ID."""
    return str(uuid.uuid4())


# ==========================================================
#  🔧 LOGGER CONFIGURATION (GLOBAL)
# ==========================================================

def configure_logging() -> None:
    """
    Configure global structured JSON logging for the entire app.
    Overrides Uvicorn and FastAPI loggers as well.
    """

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())

    root_logger.addHandler(handler)

    # Unify Uvicorn loggers with our JSON format
    logging.getLogger("uvicorn.error").handlers = [handler]
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("uvicorn").handlers = [handler]

    # Reduce noisy logs
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    root_logger.info("Logging configured successfully", extra={"event": "logging_setup"})


# ==========================================================
#  📦 LOGGER ACCESSOR
# ==========================================================

def get_logger(name: str) -> logging.Logger:
    """Get a JSON-structured logger."""
    return logging.getLogger(name)


# ==========================================================
#  🧪 TEST HOOK (used in pytest to reinitialize logging)
# ==========================================================

def reset_logging_for_tests() -> None:
    """Reset logging system for clean test behavior."""
    logging.shutdown()
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

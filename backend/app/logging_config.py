import logging
import contextvars
from logging.config import dictConfig
from typing import Optional

# Context variables for request tracing
request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)
consent_trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "consent_trace_id", default=None
)


class RequestContextFilter(logging.Filter):
    """Attach tracing IDs to every log line."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or ""
        record.consent_trace_id = consent_trace_id_var.get() or ""
        return True

def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_context": {"()": RequestContextFilter},
            },
            "formatters": {
                "json": {
                    "format": (
                        '{"timestamp":"%(asctime)s",'
                        '"level":"%(levelname)s",'
                        '"logger":"%(name)s",'
                        '"message":"%(message)s",'
                        '"request_id":"%(request_id)s",'
                        '"consent_trace_id":"%(consent_trace_id)s"}'
                    )
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "filters": ["request_context"],
                }
            },
            "root": {
                "handlers": ["console"],
                "level": "INFO",
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
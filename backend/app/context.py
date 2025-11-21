# backend/app/context.py

import contextvars

# These context variables store request-level data (per request)
request_id_var = contextvars.ContextVar("request_id", default="")
consent_trace_id_var = contextvars.ContextVar("consent_trace_id", default="")

class TraceContext:
    @property
    def request_id(self) -> str:
        return request_id_var.get()

    @request_id.setter
    def request_id(self, value: str):
        request_id_var.set(value)

    @property
    def consent_trace_id(self) -> str:
        return consent_trace_id_var.get()

    @consent_trace_id.setter
    def consent_trace_id(self, value: str):
        consent_trace_id_var.set(value)

# Global instance used everywhere
trace_context = TraceContext()


def clear_trace_context():
    """Used in tests to reset context before each request."""
    request_id_var.set("")
    consent_trace_id_var.set("")

# backend/app/middleware/request_context_middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from backend.app.logging_config import set_request_id, set_consent_trace_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that reads X-Request-Id and X-Consent-Trace-Id from incoming headers
    and attaches them to request.state (and contextvars) if present.
    It intentionally does NOT generate IDs; TraceMiddleware handles generation.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            rid = request.headers.get("x-request-id") or request.headers.get("X-Request-Id")
            cid = request.headers.get("x-consent-trace-id") or request.headers.get("X-Consent-Trace-Id")

            if rid:
                # attach to request.state for endpoint access
                request.state.request_id = rid
                set_request_id(rid)
            else:
                # ensure attributes exist even if not provided
                request.state.request_id = None

            if cid:
                request.state.consent_trace_id = cid
                set_consent_trace_id(cid)
            else:
                request.state.consent_trace_id = None

            response = await call_next(request)
            return response
        finally:
            # Do not clear context here; TraceMiddleware or tests control lifecycle
            pass

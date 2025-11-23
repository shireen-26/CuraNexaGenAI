# backend/app/middleware/trace_middleware.py

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.logging_config import (
    set_request_id,
    set_consent_trace_id,
    get_request_id,
    get_consent_trace_id,
    get_logger,
)

logger = get_logger("trace-middleware")


class TraceMiddleware(BaseHTTPMiddleware):
    """
    Ensures a request_id exists (generates a UUID when missing), sets contextvars,
    echoes headers back on the response, and logs via the JSON adapter.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            # Prefer header; else use existing contextvar; else generate
            rid = request.headers.get("x-request-id") or request.headers.get("X-Request-Id") or get_request_id() or str(uuid.uuid4())
            cid = request.headers.get("x-consent-trace-id") or request.headers.get("X-Consent-Trace-Id") or get_consent_trace_id() or ""

            # set into contextvars (so adapter picks them up)
            set_request_id(rid)
            set_consent_trace_id(cid)

            # also attach to request.state so endpoints see them (if RequestContextMiddleware didn't)
            request.state.request_id = rid
            request.state.consent_trace_id = cid

            # log a lifecycle message (adapter will include request_id)
            logger.info("request_received")

            response: Response = await call_next(request)

            # echo headers back
            response.headers["X-Request-Id"] = rid
            if cid:
                response.headers["X-Consent-Trace-Id"] = cid

            logger.info("response_started")
            logger.info("request_completed")

            return response
        finally:
            # Clear context to avoid leaking between requests
            set_request_id(None)
            set_consent_trace_id(None)

TraceContextMiddleware = TraceMiddleware
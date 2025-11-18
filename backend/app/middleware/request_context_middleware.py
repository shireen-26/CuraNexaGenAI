import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging_config import get_logger

logger = get_logger("request_context")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures each request has:
    - X-Request-Id     (generated if missing)
    - X-Consent-Trace-Id (optional)
    
    Both values are attached to request.state so logging & services can use them.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Read request ID or generate one
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        consent_trace_id = request.headers.get("X-Consent-Trace-Id")

        # Attach to request.state
        request.state.request_id = request_id
        request.state.consent_trace_id = consent_trace_id

        # Log incoming request (sanitized, no PHI)
        logger.info(
            "Incoming request",
            extra={
                "event": "incoming_request",
                "extra_data": {
                    "method": request.method,
                    "path": request.url.path,
                    "request_id": request_id,
                    "consent_trace_id": consent_trace_id,
                },
                "trace_id": request_id,
            },
        )

        # Process request
        response: Response = await call_next(request)

        # Add IDs to response headers
        response.headers["X-Request-Id"] = request_id
        if consent_trace_id:
            response.headers["X-Consent-Trace-Id"] = consent_trace_id

        return response

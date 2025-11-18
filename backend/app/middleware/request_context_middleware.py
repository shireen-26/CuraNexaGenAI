import uuid
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from backend.app.logging_config import get_logger

logger = get_logger("request_context")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures each request has:
    - X-Request-Id (generated if missing)
    - X-Consent-Trace-Id (optional)
    Both stored in request.state for logging and services.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Read or create request ID
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        consent_trace_id = request.headers.get("X-Consent-Trace-Id")

        # Attach to request.state
        request.state.request_id = request_id
        request.state.consent_trace_id = consent_trace_id

        # Log the incoming request
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

        # Continue to the next handler
        response: Response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-Id"] = request_id
        if consent_trace_id:
            response.headers["X-Consent-Track-Id"] = consent_trace_id

        return response

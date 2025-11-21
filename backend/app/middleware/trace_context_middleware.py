# backend/app/middleware/trace_context_middleware.py

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.core.logging_config import (
    set_request_id,
    set_consent_trace_id,
    clear_trace_context,
    get_logger,
)


logger = get_logger("trace-middleware")


class TraceContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            incoming_req_id = request.headers.get("X-Request-Id")
            if not incoming_req_id:
                incoming_req_id = str(uuid.uuid4())

            incoming_consent = request.headers.get("X-Consent-Trace-Id", "")

            # store in contextvars
            set_request_id(incoming_req_id)
            set_consent_trace_id(incoming_consent)

            # log request start
            logger.info("request_received")

            response: Response = await call_next(request)

            # include IDs back to client
            response.headers["X-Request-Id"] = incoming_req_id

            logger.info("response_started")
            logger.info("request_completed")

            return response

        finally:
            clear_trace_context()

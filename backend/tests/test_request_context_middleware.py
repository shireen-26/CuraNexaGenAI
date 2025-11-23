# backend/app/middleware/request_context_middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import HTTPException
import warnings

from backend.app.logging_config import set_request_id, set_consent_trace_id, get_logger

logger = get_logger("request-context-middleware")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that reads X-Request-Id and X-Consent-Trace-Id from incoming headers
    and attaches them to request.state (and contextvars) if present.
    It intentionally does NOT generate IDs; TraceMiddleware handles generation.
    """

    async def dispatch(self, request: Request, call_next):
        rid = None
        cid = None

        try:
            # read headers in a case-insensitive manner
            rid = request.headers.get("x-request-id") or request.headers.get("X-Request-Id")
            cid = request.headers.get("x-consent-trace-id") or request.headers.get("X-Consent-Trace-Id")

            if rid:
                # attach to request.state for endpoint access and central context
                request.state.request_id = rid
                set_request_id(rid)
                logger.info(
                    "attached_request_id",
                    extra={"extra_fields": {"operation": "attach_request_context", "request_id": rid}},
                )
            else:
                # ensure attributes exist even if not provided
                request.state.request_id = None
                # not an error — just informative
                logger.info(
                    "no_request_id_provided",
                    extra={"extra_fields": {"operation": "attach_request_context", "request_id": None}},
                )

            if cid:
                request.state.consent_trace_id = cid
                set_consent_trace_id(cid)
                logger.info(
                    "attached_consent_trace_id",
                    extra={"extra_fields": {"operation": "attach_request_context", "consent_trace_id": cid}},
                )
            else:
                request.state.consent_trace_id = None
                logger.info(
                    "no_consent_trace_id_provided",
                    extra={"extra_fields": {"operation": "attach_request_context", "consent_trace_id": None}},
                )

            # mild hardening: warn if IDs look obviously malformed (too long)
            if rid and len(rid) > 200:
                warnings.warn("Received unusually long X-Request-Id header", UserWarning)
                logger.warning(
                    "suspicious_request_id_length",
                    extra={"extra_fields": {"operation": "attach_request_context", "request_id": rid}},
                )

            response = await call_next(request)

            # echo headers back if present on request.state (safe: IDs only)
            try:
                if getattr(request.state, "request_id", None):
                    response.headers.setdefault("X-Request-Id", request.state.request_id)
                if getattr(request.state, "consent_trace_id", None):
                    response.headers.setdefault("X-Consent-Trace-Id", request.state.consent_trace_id)
            except Exception:
                # non-fatal: log but do not break response
                logger.error(
                    "failed_to_set_response_headers",
                    extra={"extra_fields": {"operation": "attach_request_context", "request_id": rid, "consent_trace_id": cid}},
                    exc_info=True,
                )

            logger.info(
                "request_context_dispatched",
                extra={"extra_fields": {"operation": "dispatch_complete", "request_id": rid, "consent_trace_id": cid}},
            )
            return response

        except HTTPException:
            # expected HTTP errors should be re-raised after logging as warnings
            logger.warning(
                "http_exception_in_dispatch",
                extra={"extra_fields": {"operation": "dispatch", "request_id": rid}},
            )
            raise

        except Exception as exc:
            # unexpected errors: log full traceback and convert to generic HTTP 500
            logger.error(
                "unexpected_error_in_request_context_middleware",
                extra={"extra_fields": {"operation": "dispatch", "request_id": rid, "consent_trace_id": cid}},
                exc_info=True,
            )
            # Avoid leaking any internal details
            raise HTTPException(status_code=500, detail="Internal Server Error") from exc

        finally:
            # Intentionally not clearing contextvars here; lifecycle is managed elsewhere.
            pass

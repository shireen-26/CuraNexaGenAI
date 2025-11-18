import logging
from fastapi import FastAPI, Request
from starlette.testclient import TestClient

from backend.app.middleware.request_context_middleware import RequestContextMiddleware
from backend.app.logging_config import configure_logging, get_logger

def test_logging_includes_trace_fields(caplog):
    configure_logging()
    logger = get_logger("test_logger")

    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/log-test")
    async def log_test(request: Request):
        logger.info(
            "Test log message",
            extra={"trace_id": request.state.request_id},
        )
        return {"ok": True}

    client = TestClient(app)

    req_id = "request-xyz"
    consent_id = "trace-777"

    with caplog.at_level(logging.INFO):
        response = client.get(
            "/log-test",
            headers={
                "X-Request-Id": req_id,
                "X-Consent-Trace-Id": consent_id,
            },
        )

    assert response.status_code == 200

    logs = "\n".join(record.message for record in caplog.records)
    assert "Test log message" in logs
    assert req_id in logs

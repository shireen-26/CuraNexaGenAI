import json
import logging
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from backend.app.logging_config import configure_logging, get_logger
from backend.app.middleware.request_context_middleware import RequestContextMiddleware
from backend.app.middleware.trace_middleware import TraceMiddleware


def extract_json_logs(caplog):
    logs = []
    for rec in caplog.records:
        try:
            logs.append(json.loads(rec.msg))
        except:
            pass
    return logs


def test_logging_includes_trace_fields(caplog):
    configure_logging()
    logger = get_logger("test_logger")

    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(TraceMiddleware)

    @app.get("/log-test")
    async def log_test(request: Request):
        logger.info("Test log message")
        return {"ok": True}

    client = TestClient(app)

    with caplog.at_level(logging.INFO):
        response = client.get(
            "/log-test",
            headers={
                "X-Request-Id": "request-xyz",
                "X-Consent-Trace-Id": "trace-777",
            },
        )

    assert response.status_code == 200

    logs = extract_json_logs(caplog)
    messages = [l.get("message") for l in logs]

    assert "Test log message" in messages

import json
import logging
import re
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.logging_config import (
    configure_logging,
    get_logger,
    clear_trace_context,
)
from backend.app.middleware.trace_middleware import TraceMiddleware


def extract_json_logs(caplog):
    logs = []
    for r in caplog.records:
        try:
            logs.append(json.loads(r.msg))
        except:
            pass
    return logs


def test_generated_request_id_and_json_logs(caplog):
    configure_logging()
    logger = get_logger("test_logger_generated")

    app = FastAPI()
    app.add_middleware(TraceMiddleware)

    @app.get("/ping")
    async def ping():
        logger.info("pinged")
        return {"ok": True}

    client = TestClient(app)

    clear_trace_context()

    with caplog.at_level(logging.INFO):
        resp = client.get("/ping")

    assert resp.status_code == 200

    log_req_id = resp.headers["X-Request-Id"]
    assert re.match(r"^[0-9a-fA-F-]{32,36}$", log_req_id)

    logs = extract_json_logs(caplog)
    assert any(l.get("request_id") == log_req_id for l in logs)


def test_preserve_request_and_consent_ids(caplog):
    configure_logging()
    logger = get_logger("test_logger_preserve")

    app = FastAPI()
    app.add_middleware(TraceMiddleware)

    @app.get("/ping")
    async def ping():
        logger.info("pinged")
        return {"ok": True}

    client = TestClient(app)

    with caplog.at_level(logging.INFO):
        resp = client.get(
            "/ping",
            headers={
                "X-Request-Id": "custom-123",
                "X-Consent-Trace-Id": "consent-999",
            },
        )

    assert resp.headers["X-Request-Id"] == "custom-123"
    assert resp.headers["X-Consent-Trace-Id"] == "consent-999"

    logs = extract_json_logs(caplog)
    assert any(l.get("request_id") == "custom-123" for l in logs)

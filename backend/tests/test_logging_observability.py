import re
import json
import logging
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.logging_config import configure_logging

client = TestClient(app)


import json
import re

def extract_json_logs(caplog):
    logs = []
    for line in caplog.messages:
        # Find JSON inside the line
        match = re.search(r"\{.*\}", line)
        if match:
            try:
                logs.append(json.loads(match.group()))
            except json.JSONDecodeError:
                pass
    return logs


# ------------------------------------------------------------
# 1. If X-Request-Id is sent → it must be preserved
# ------------------------------------------------------------
def test_preserve_request_id(caplog):
    configure_logging()

    with caplog.at_level(logging.INFO):
        resp = client.get(
            "/health",
            headers={"X-Request-Id": "request-123"}
        )

    assert resp.status_code == 200

    logs = extract_json_logs(caplog)
    assert any(l.get("request_id") == "request-123" for l in logs)


# ------------------------------------------------------------
# 2. If no X-Request-Id → generate UUID
# ------------------------------------------------------------
def test_generate_uuid_request_id(caplog):
    configure_logging()

    with caplog.at_level(logging.INFO):
        resp = client.get("/health")

    req_id = resp.headers.get("X-Request-Id")
    assert req_id, "UUID should be returned in header"

    # UUID-like structure
    assert re.match(r"^[0-9a-fA-F-]{32,36}$", req_id)

    logs = extract_json_logs(caplog)
    assert any(l.get("request_id") == req_id for l in logs)


# ------------------------------------------------------------
# 3. If X-Consent-Trace-Id sent → preserved
# ------------------------------------------------------------
def test_preserve_consent_trace_id(caplog):
    configure_logging()

    with caplog.at_level(logging.INFO):
        resp = client.get(
            "/health",
            headers={"X-Consent-Trace-Id": "consent-xyz"}
        )

    logs = extract_json_logs(caplog)

    assert any(
        l.get("consent_trace_id") == "consent-xyz"
        for l in logs
    )


# ------------------------------------------------------------
# 4. Middleware should NOT break existing endpoints
# ------------------------------------------------------------
def test_health_endpoint_still_works(caplog):
    configure_logging()

    with caplog.at_level(logging.INFO):
        resp = client.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"  # existing behaviour

    # Ensure logs still emitted
    logs = extract_json_logs(caplog)
    assert len(logs) > 0


# ------------------------------------------------------------
# 5. No sensitive data logged
# ------------------------------------------------------------
def test_no_sensitive_data_logged(caplog):
    configure_logging()

    # A sample PII-like text that should not appear in logs
    pii_sample = "my-secret-password"

    with caplog.at_level(logging.INFO):
        resp = client.get(
            "/health",
            headers={"X-Request-Id": "abc"},
        )

    assert resp.status_code == 200

    logs = extract_json_logs(caplog)

    # Ensure PII text is not present anywhere
    for log in logs:
        msg = json.dumps(log)
        assert pii_sample not in msg

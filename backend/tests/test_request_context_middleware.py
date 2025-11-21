import uuid
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from backend.app.middleware.request_context_middleware import RequestContextMiddleware


def test_request_context_middleware_attaches_ids():
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/test")
    async def test_endpoint(request: Request):
        return {
            "request_id": request.state.request_id,
            "consent_id": request.state.consent_trace_id,
        }

    client = TestClient(app)

    req_id = str(uuid.uuid4())
    consent_id = "abc-123-trace"

    response = client.get(
        "/test",
        headers={
            "X-Request-Id": req_id,
            "X-Consent-Trace-Id": consent_id,
        },
    )

    body = response.json()
    assert body["request_id"] == req_id
    assert body["consent_id"] == consent_id

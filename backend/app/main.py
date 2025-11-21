# backend/app/main.py

from fastapi import FastAPI
from backend.app.core.logging_config import (
    configure_logging,
    get_logger,
    get_request_id,
    get_consent_trace_id,
)

configure_logging()

from backend.app.middleware.trace_context_middleware import TraceContextMiddleware

app = FastAPI()
app.add_middleware(TraceContextMiddleware)

logger = get_logger("app-main")


@app.get("/health")
async def health():
    logger.info("health_check")
    return {"status": "ok"}

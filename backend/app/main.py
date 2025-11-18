from fastapi import FastAPI
from backend.app.logging_config import configure_logging

from backend.app.middleware.request_context_middleware import RequestContextMiddleware


configure_logging()

app = FastAPI()

from fastapi import FastAPI, Request
from backend.app.logging_config import get_logger
from backend.app.middleware.request_context_middleware import RequestContextMiddleware

app = FastAPI()

# Attach middleware
app.add_middleware(RequestContextMiddleware)

logger = get_logger("health")


@app.get("/health")
async def health_check(request: Request):
    logger.info(
        "Health check OK",
        extra={
            "trace_id": request.state.request_id,
            "method": request.method,
            "path": request.url.path,
        }
    )
    return {"status": "healthy"}

# Register middleware
app.add_middleware(RequestContextMiddleware)

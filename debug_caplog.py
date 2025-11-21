# debug_caplog.py (place in project root)
import sys
import os

# ensure project root is on sys.path so imports find files in the repo root
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import your logging and middleware modules (adjust names if yours differ)
from logging_config import configure_logging, get_logger
from trace_middleware import TraceMiddleware

from fastapi import FastAPI
from fastapi.testclient import TestClient

# configure logging
configure_logging()
logger = get_logger("debug_logger")

app = FastAPI()
# add middleware (this expects the class TraceMiddleware in trace_middleware.py)
app.add_middleware(TraceMiddleware)

@app.get("/ping")
def ping():
    logger.info("hello-debug")
    return {"ok": True}

if __name__ == "__main__":
    client = TestClient(app)
    resp = client.get("/ping")
    print("resp.status_code:", resp.status_code)
    print("resp.headers:", dict(resp.headers))

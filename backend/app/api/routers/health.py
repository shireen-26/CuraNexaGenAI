# backend/app/api/routers/health.py
from fastapi import APIRouter
from app.lib.logger import get_logger

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger("health-router")

@router.get("", summary="Health check")
async def health():
    """
    Simple health check endpoint.
    Logs a non-PHI health-check event using structured logger.
    """
    logger.info("health_check", extra={"status":"ok"})
    return {"status": "ok"}

import logging

from fastapi import APIRouter

from app.db.connection import oracle_db, redis_db
from app.schemas.api import HealthResponse, RootResponse

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    """
    Root endpoint providing API information.

    Returns:
        RootResponse with API metadata and available endpoints
    """
    logger.debug("Root endpoint accessed")

    return RootResponse(
        message="SSE Streaming Server",
        version="0.1.0",
        endpoints={
            "stream": "/stream/{type}",
            "stream_db": "/stream/database",
            "stream_redis": "/stream/redis/{channel}",
            "oracle_telemetry": "/stream/oracle/telemetry",
            "oracle_orders": "/stream/oracle/orders/changes",
            "chat": "/chat/stream",
        },
    )


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse with service status and database connectivity
    """
    oracle_healthy = oracle_db.connection is not None
    redis_healthy = redis_db.client is not None

    overall_status = "healthy" if (oracle_healthy or redis_healthy) else "degraded"

    logger.info(f"Health check: {overall_status} (Oracle: {oracle_healthy}, Redis: {redis_healthy})")

    return HealthResponse(
        status=overall_status,
        oracle=oracle_healthy,
        redis=redis_healthy,
    )

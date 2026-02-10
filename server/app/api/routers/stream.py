import logging

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.db.streaming_helpers import get_session_factory
from app.schemas.api import (
    DatabaseStreamRequest,
    OracleOrdersStreamRequest,
    OracleTelemetryStreamRequest,
)
from app.services.generic_streaming import stream_data_generator
from app.services.oracle_streaming import (
    stream_database_data,
    stream_oracle_orders_changes_data,
    stream_oracle_telemetry_data,
)
from app.services.redis_streaming import stream_redis_data

router = APIRouter(prefix="/stream", tags=["Stream"])
logger = logging.getLogger(__name__)


@router.post("/database")
async def stream_database(
    request: DatabaseStreamRequest,
    session_factory=Depends(get_session_factory),
) -> EventSourceResponse:
    """
    Stream data from Oracle database.

    Returns:
        EventSourceResponse with database time and count
    """
    logger.info("Starting database stream")
    return EventSourceResponse(stream_database_data(session_factory))


@router.post("/oracle/telemetry")
async def stream_oracle_telemetry(
    request: OracleTelemetryStreamRequest,
    session_factory=Depends(get_session_factory),
) -> EventSourceResponse:
    """
    Stream telemetry from Oracle (db_time, object_count, query_ms).

    Returns:
        EventSourceResponse with Oracle telemetry data
    """
    logger.info("Starting Oracle telemetry stream")
    return EventSourceResponse(stream_oracle_telemetry_data(session_factory))


@router.post("/oracle/orders/changes")
async def stream_oracle_orders_changes(
    request: OracleOrdersStreamRequest,
    session_factory=Depends(get_session_factory),
) -> EventSourceResponse:
    """
    Stream change events from ORDERS (new rows + status changes).

    Args:
        request: Stream configuration (limit, poll_interval)
        session_factory: Database session factory

    Returns:
        EventSourceResponse with order change events
    """
    logger.info(f"Starting Oracle orders stream (limit={request.limit}, interval={request.poll_interval})")
    return EventSourceResponse(
        stream_oracle_orders_changes_data(
            session_factory=session_factory,
            limit=request.limit,
            poll_interval=request.poll_interval,
        )
    )


@router.get("/redis/{channel}")
async def stream_redis(channel: str) -> EventSourceResponse:
    """
    Stream data from Redis pub/sub.

    Args:
        channel: Redis channel to subscribe to

    Returns:
        EventSourceResponse with Redis pub/sub messages
    """
    logger.info(f"Starting Redis stream for channel: {channel}")
    return EventSourceResponse(stream_redis_data(channel))


@router.get("/{stream_type}")
async def stream_endpoint(stream_type: str) -> EventSourceResponse:
    """
    SSE streaming endpoint for generic data streams.

    Args:
        stream_type: Type of stream (counter, timestamp, custom)

    Returns:
        EventSourceResponse with stream data
    """
    logger.info(f"Starting generic stream: {stream_type}")
    return EventSourceResponse(stream_data_generator(stream_type))

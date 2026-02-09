import json
import logging

from fastapi import APIRouter, HTTPException

from app.db.connection import redis_db
from app.schemas.api import (
    PublishErrorResponse,
    PublishMessageRequest,
    PublishMessageResponse,
)

router = APIRouter(prefix="/publish", tags=["Redis"])
logger = logging.getLogger(__name__)


@router.post("/{channel}", response_model=PublishMessageResponse)
async def publish_to_redis(
    channel: str, request: PublishMessageRequest
) -> PublishMessageResponse:
    """
    Publish message to Redis channel.

    Args:
        channel: Redis channel to publish to
        request: Message payload to publish

    Returns:
        PublishMessageResponse with status and message details

    Raises:
        HTTPException: If Redis client is not available or publish fails
    """
    try:
        redis_client = redis_db.get_client()
        if redis_client is None:
            logger.error("Redis client is not connected")
            raise HTTPException(
                status_code=503, detail="Redis service is not available"
            )

        # Publish message to Redis
        redis_client.publish(channel, json.dumps(request.message))

        logger.info(f"Published message to Redis channel: {channel}")

        return PublishMessageResponse(
            status="published", channel=channel, message=request.message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish to Redis channel {channel}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to publish message: {str(e)}"
        ) from e

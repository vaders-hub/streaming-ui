import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime

from app.schemas.streaming import ErrorData

logger = logging.getLogger(__name__)

DEFAULT_REDIS_POLL_INTERVAL = 0.1
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 1.0


def _create_event_data(event_type: str, payload: dict) -> dict[str, str]:
    """Helper to create SSE event data."""
    return {
        "event": "message",
        "data": json.dumps(
            {
                "type": event_type,
                "timestamp": datetime.now().isoformat(),
                **payload,
            }
        ),
    }


def _create_error_response(error: Exception) -> dict[str, str]:
    """Helper to create error response."""
    error_data: ErrorData = {
        "type": "error",
        "error": str(error),
        "timestamp": datetime.now().isoformat(),
    }
    return {
        "event": "error",
        "data": json.dumps(error_data),
    }


def _fetch_redis_message(pubsub):
    """Fetch Redis message."""
    return pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1)


async def stream_redis_data(
    channel: str = "updates",
    poll_interval: float = DEFAULT_REDIS_POLL_INTERVAL,
) -> AsyncGenerator[dict[str, str], None]:
    """Stream data from Redis pub/sub."""
    from app.db.connection import redis_db

    pubsub = None
    retry_count = 0

    try:
        redis_client = redis_db.get_client()
        if redis_client is None:
            raise RuntimeError("Redis client is not connected")

        pubsub = redis_client.pubsub()
        pubsub.subscribe(channel)

        logger.info(f"Subscribed to Redis channel: {channel}")

        while True:
            try:
                # 동기 Redis 작업을 별도 스레드에서 실행하여 이벤트 루프 블로킹 방지
                message = await asyncio.to_thread(_fetch_redis_message, pubsub)

                if message and message["type"] == "message":
                    yield _create_event_data(
                        "redis",
                        {"channel": channel, "message": message["data"]},
                    )

                    retry_count = 0

                await asyncio.sleep(poll_interval)

            except asyncio.CancelledError:
                logger.info(f"Redis stream cancelled by client/server for channel: {channel}")
                raise
            except Exception as e:
                retry_count += 1
                logger.error(
                    f"Error in Redis stream for {channel} (Attempt {retry_count}/{MAX_RETRY_ATTEMPTS}): {e}",
                    exc_info=True,
                )

                yield _create_error_response(e)

                if retry_count >= MAX_RETRY_ATTEMPTS:
                    logger.error("Max retry attempts reached. Stopping stream.")
                    break

                await asyncio.sleep(RETRY_DELAY * retry_count)

    except Exception as e:
        logger.error(f"Fatal error in Redis stream setup: {e}", exc_info=True)
        yield _create_error_response(e)
    finally:
        if pubsub is not None:
            try:
                pubsub.unsubscribe(channel)
                pubsub.close()
                logger.info(f"Unsubscribed from Redis channel: {channel}")
            except Exception as e:
                logger.error(f"Error cleaning up Redis pubsub: {e}", exc_info=True)

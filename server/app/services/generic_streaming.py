import asyncio
import json
import logging
from collections.abc import AsyncGenerator, Callable
from datetime import datetime

from app.schemas.streaming import (
    CounterData,
    CustomData,
    ErrorData,
    TimestampData,
)

logger = logging.getLogger(__name__)

DEFAULT_COUNTER_INTERVAL = 1.0
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


def _create_counter_data(count: int) -> dict:
    """Create counter data."""
    return {
        "count": count,
    }


def _create_timestamp_data(count: int) -> dict:
    """Create timestamp data."""
    return {
        "current_time": datetime.now().isoformat(),
        "message": f"Server time update #{count}",
    }


def _create_custom_data(count: int) -> dict:
    """Create custom data."""
    return {
        "data": f"Custom data #{count}",
    }


DATA_GENERATORS: dict[str, Callable[[int], CounterData | TimestampData | CustomData]] = {
    "counter": _create_counter_data,
    "timestamp": _create_timestamp_data,
    "custom": _create_custom_data,
}


async def stream_data_generator(
    data_type: str = "counter",
    interval: float = DEFAULT_COUNTER_INTERVAL,
) -> AsyncGenerator[dict[str, str], None]:
    """Generic SSE data generator."""
    generator_func = DATA_GENERATORS.get(data_type)
    if generator_func is None:
        error_msg = f"Unsupported data_type: {data_type}. Available types: {', '.join(DATA_GENERATORS.keys())}"
        logger.error(error_msg)
        yield _create_error_response(ValueError(error_msg))
        return

    count = 0

    try:
        while True:
            try:
                payload = generator_func(count)
                yield _create_event_data(data_type, payload)

                count += 1
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info(f"Stream cancelled for {data_type}")
                raise
            except Exception as e:
                logger.error(f"Error in stream for {data_type}: {e}", exc_info=True)
                yield _create_error_response(e)
                await asyncio.sleep(RETRY_DELAY)
    finally:
        logger.info(f"Stream {data_type} shutting down")

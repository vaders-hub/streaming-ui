import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models import Order
from app.schemas.streaming import ErrorData

logger = logging.getLogger(__name__)

DEFAULT_DB_POLL_INTERVAL = 2.0
DEFAULT_ORDERS_LIMIT = 50
DEFAULT_ORDERS_POLL_INTERVAL = 2.0
DEFAULT_HEARTBEAT_INTERVAL = 15.0
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


def _fetch_db_time(session_factory: Callable[[], AbstractContextManager[Session]]) -> datetime | None:
    """Fetch database time."""
    with session_factory() as session:
        result = session.execute(text("SELECT SYSDATE FROM DUAL")).fetchone()
        return result[0] if result else None


def _fetch_oracle_telemetry(
    session_factory: Callable[[], AbstractContextManager[Session]],
) -> tuple[str | None, int | None, float]:
    """Fetch Oracle telemetry."""
    with session_factory() as session:
        start = time.perf_counter()
        result = session.execute(
            text(
                """
                SELECT
                    TO_CHAR(
                        SYSTIMESTAMP,
                        'YYYY-MM-DD"T"HH24:MI:SS.FF3TZH:TZM'
                    ) AS db_time,
                    (SELECT COUNT(*) FROM USER_OBJECTS) AS object_count
                FROM dual
                """
            )
        )
        row = result.fetchone()
        elapsed_ms = (time.perf_counter() - start) * 1000

        db_time = row[0] if row else None
        object_count = int(row[1]) if row and row[1] is not None else None

        return db_time, object_count, elapsed_ms


def _fetch_latest_orders(
    session_factory: Callable[[], AbstractContextManager[Session]], limit: int
) -> list[dict]:
    """Fetch latest orders."""
    with session_factory() as session:
        stmt = select(Order).order_by(Order.order_id.desc()).limit(limit)
        orders = session.scalars(stmt).all()
        return [
            {
                "order_id": order.order_id,
                "customer_id": order.customer_id,
                "status": order.status,
                "salesman_id": order.salesman_id,
                "order_date": order.order_date.isoformat() if order.order_date else None,
            }
            for order in orders
        ]


def _fetch_new_orders_since(
    session_factory: Callable[[], AbstractContextManager[Session]], last_max_id: int
) -> list[dict]:
    """Fetch new orders since ID."""
    with session_factory() as session:
        stmt = select(Order).where(Order.order_id > last_max_id).order_by(Order.order_id)
        orders = session.scalars(stmt).all()
        return [
            {
                "order_id": order.order_id,
                "customer_id": order.customer_id,
                "status": order.status,
                "salesman_id": order.salesman_id,
                "order_date": order.order_date.isoformat() if order.order_date else None,
            }
            for order in orders
        ]


def _fetch_initial_order_status(
    session_factory: Callable[[], AbstractContextManager[Session]], limit: int
) -> tuple[dict[int, str], int]:
    """Fetch initial order status snapshot."""
    orders = _fetch_latest_orders(session_factory, limit)
    status_map = {}
    for order in orders:
        status_map[order["order_id"]] = order["status"]
    max_id = max(status_map.keys()) if status_map else 0
    return status_map, max_id


async def stream_database_data(
    session_factory: Callable[[], AbstractContextManager[Session]],
    poll_interval: float = DEFAULT_DB_POLL_INTERVAL,
) -> AsyncGenerator[dict[str, str], None]:
    """Stream data from Oracle database."""
    count = 0
    retry_count = 0

    try:
        while True:
            try:
                db_time = await asyncio.to_thread(_fetch_db_time, session_factory)

                yield _create_event_data(
                    "database", {"count": count, "db_time": str(db_time) if db_time else None}
                )

                count += 1
                retry_count = 0
                await asyncio.sleep(poll_interval)

            except asyncio.CancelledError:
                logger.info("Database stream cancelled by client/server")
                raise
            except Exception as e:
                retry_count += 1
                logger.error(
                    f"Error in database stream (Attempt {retry_count}/{MAX_RETRY_ATTEMPTS}): {e}",
                    exc_info=True,
                )

                yield _create_error_response(e)

                if retry_count >= MAX_RETRY_ATTEMPTS:
                    logger.error("Max retry attempts reached. Stopping stream.")
                    break
                await asyncio.sleep(RETRY_DELAY * retry_count)
    finally:
        logger.info("Database stream resources cleaned up")


async def stream_oracle_telemetry_data(
    session_factory: Callable[[], AbstractContextManager[Session]],
    poll_interval: float = DEFAULT_DB_POLL_INTERVAL,
) -> AsyncGenerator[dict[str, str], None]:
    """Stream telemetry from Oracle."""
    count = 0
    retry_count = 0

    try:
        while True:
            try:
                db_time, object_count, elapsed_ms = await asyncio.to_thread(
                    _fetch_oracle_telemetry, session_factory
                )

                yield _create_event_data(
                    "oracle_telemetry",
                    {
                        "count": count,
                        "db_time": db_time,
                        "object_count": object_count,
                        "query_ms": round(elapsed_ms, 2),
                    },
                )

                count += 1
                retry_count = 0
                await asyncio.sleep(poll_interval)

            except asyncio.CancelledError:
                logger.info("Oracle telemetry stream cancelled by client/server")
                raise
            except Exception as e:
                retry_count += 1
                logger.error(
                    f"Error in oracle telemetry stream (Attempt {retry_count}/{MAX_RETRY_ATTEMPTS}): {e}",
                    exc_info=True,
                )

                yield _create_error_response(e)

                if retry_count >= MAX_RETRY_ATTEMPTS:
                    logger.error("Max retry attempts reached. Stopping stream.")
                    break

                await asyncio.sleep(RETRY_DELAY * retry_count)
    finally:
        logger.info("Oracle telemetry stream resources cleaned up")


async def stream_oracle_orders_changes_data(
    session_factory: Callable[[], AbstractContextManager[Session]],
    limit: int = DEFAULT_ORDERS_LIMIT,
    poll_interval: float = DEFAULT_ORDERS_POLL_INTERVAL,
    heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL,
) -> AsyncGenerator[dict[str, str], None]:
    """Stream change events from ORDERS."""
    prev_status: dict[int, str] = {}
    last_max_id: int = 0
    last_heartbeat = time.time()
    retry_count = 0
    count = 0

    try:
        # 초기 스냅샷
        prev_status, last_max_id = await asyncio.to_thread(
            _fetch_initial_order_status, session_factory, limit
        )

        yield _create_event_data(
            "oracle_orders_ready",
            {"tracked": len(prev_status), "last_max_id": last_max_id},
        )

        while True:
            try:
                # 1) 신규 주문 조회 및 처리
                new_orders = await asyncio.to_thread(
                    _fetch_new_orders_since, session_factory, last_max_id
                )

                for order in new_orders:
                    oid = order["order_id"]
                    last_max_id = max(last_max_id, oid)
                    prev_status[oid] = order["status"]
                    yield _create_event_data(
                        "oracle_orders_change",
                        {"kind": "new", "order": order, "count": count},
                    )
                    count += 1

                # 2) 상태 변경 확인
                latest_orders = await asyncio.to_thread(
                    _fetch_latest_orders, session_factory, limit
                )
                
                latest_ids = []
                for order in latest_orders:
                    oid = order["order_id"]
                    latest_ids.append(oid)
                    new_status = order["status"]
                    old_status = prev_status.get(oid)

                    if old_status is not None and old_status != new_status:
                        prev_status[oid] = new_status
                        yield _create_event_data(
                            "oracle_orders_change",
                            {
                                "kind": "status_changed",
                                "order": {
                                    "order_id": oid,
                                    "customer_id": order["customer_id"],
                                    "old_status": old_status,
                                    "new_status": new_status,
                                    "salesman_id": order["salesman_id"],
                                    "order_date": order["order_date"],
                                },
                                "count": count,
                            },
                        )
                        count += 1
                    elif old_status is None:
                        # 새로 추적되는 주문 (범위 내 진입)
                        prev_status[oid] = new_status

                # 메모리 관리: 트래킹 목록 최신화
                keep = set(latest_ids)
                prev_status = {k: v for k, v in prev_status.items() if k in keep}

                # 하트비트 전송
                now = time.time()
                if now - last_heartbeat >= heartbeat_interval:
                    last_heartbeat = now
                    yield _create_event_data(
                        "oracle_orders_heartbeat",
                        {"tracked": len(prev_status), "last_max_id": last_max_id},
                    )

                retry_count = 0
                await asyncio.sleep(poll_interval)

            except asyncio.CancelledError:
                logger.info("Oracle orders stream cancelled by client/server")
                raise
            except Exception as e:
                retry_count += 1
                logger.error(
                    f"Error in oracle orders stream (Attempt {retry_count}/{MAX_RETRY_ATTEMPTS}): {e}",
                    exc_info=True,
                )

                yield _create_error_response(e)

                if retry_count >= MAX_RETRY_ATTEMPTS:
                    logger.error("Max retry attempts reached. Stopping stream.")
                    break

                await asyncio.sleep(RETRY_DELAY * retry_count)
    finally:
        logger.info("Oracle orders stream resources cleaned up")

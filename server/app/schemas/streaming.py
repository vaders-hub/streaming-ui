"""
TypedDict models for streaming data structures.

This module contains type definitions for various streaming data formats
used in Server-Sent Events (SSE) responses.
"""

from typing import TypedDict


class CounterData(TypedDict):
    """Counter stream data model."""

    type: str
    count: int
    timestamp: str


class TimestampData(TypedDict):
    """Timestamp stream data model."""

    type: str
    current_time: str
    message: str


class CustomData(TypedDict):
    """Custom stream data model."""

    type: str
    data: str
    timestamp: str


class DatabaseData(TypedDict):
    """Database stream data model."""

    type: str
    count: int
    db_time: str | None
    timestamp: str


class OracleTelemetryData(TypedDict):
    """Oracle telemetry stream data model."""

    type: str
    count: int
    db_time: str | None
    object_count: int | None
    query_ms: float
    timestamp: str


class ErrorData(TypedDict):
    """Error response data model."""

    type: str
    error: str
    timestamp: str


class OrderData(TypedDict):
    """Order data model."""

    order_id: int
    customer_id: int | None
    status: str
    salesman_id: int | None
    order_date: str


class OrderChangeData(TypedDict):
    """Order change event data model."""

    type: str
    kind: str
    order: OrderData
    count: int
    timestamp: str


class RedisData(TypedDict):
    """Redis pub/sub stream data model."""

    type: str
    channel: str
    message: bytes | str
    timestamp: str

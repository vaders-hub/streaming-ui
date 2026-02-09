"""
Pydantic models for API request/response schemas.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# Type aliases
OrderStatus = Literal["PENDING", "SHIPPED", "CANCELLED", "COMPLETE"]
ChunkMode = Literal["token", "chars", "paragraph"]


# Oracle API Models
class CreateOrderRequest(BaseModel):
    """Request model for creating a new order."""

    customer_id: int = Field(..., ge=1, description="Customer ID (must be >= 1)")
    status: str = Field(
        "PENDING", min_length=1, max_length=20, description="Order status"
    )
    salesman_id: int | None = Field(
        default=None, ge=1, description="Salesman ID (optional)"
    )


class OracleOrdersStreamRequest(BaseModel):
    """Request body for POST /stream/oracle/orders/changes."""
    
    limit: int = Field(50, ge=1, le=500, description="Max orders to track")
    poll_interval: float = Field(2.0, ge=0.2, le=30.0, description="Poll interval in seconds")


class OracleTelemetryStreamRequest(BaseModel):
    """Request body for POST /stream/oracle/telemetry."""
    pass


class DatabaseStreamRequest(BaseModel):
    """Request body for POST /stream/database."""
    pass


class UpdateOrderStatusRequest(BaseModel):
    """Request model for updating order status."""

    status: str = Field(..., min_length=1, max_length=20, description="New order status")


class CreateOrderResponse(BaseModel):
    """Response model for order creation."""

    ok: bool
    order_id: int
    customer_id: int
    status: str
    salesman_id: int | None
    order_date: str


class UpdateOrderStatusResponse(BaseModel):
    """Response model for order status update."""

    ok: bool
    order_id: int
    old_status: str
    new_status: str


# Redis API Models
class PublishMessageRequest(BaseModel):
    """Request model for publishing message to Redis."""

    message: dict = Field(..., description="Message to publish as JSON")


class PublishMessageResponse(BaseModel):
    """Response model for Redis publish operation."""

    status: str
    channel: str
    message: dict


class PublishErrorResponse(BaseModel):
    """Error response model for Redis publish operation."""

    status: str
    error: str


# Chat API Models
class ChatRequest(BaseModel):
    """Request body for POST /chat/stream."""

    prompt: str = Field(..., min_length=1, description="User prompt")
    mode: ChunkMode = Field(
        "token", description="Chunking mode: token, chars, or paragraph"
    )
    chunk_size: int = Field(
        80, ge=1, le=2000, description="Chunk size for chars/paragraph mode"
    )


# Health API Models
class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    oracle: bool
    redis: bool


class RootResponse(BaseModel):
    """Response model for root endpoint."""

    message: str
    version: str
    endpoints: dict[str, str]

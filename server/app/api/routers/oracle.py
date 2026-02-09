import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import RecordNotFoundError, handle_db_error
from app.db.dependencies import get_db
from app.db.models import Order
from app.schemas.api import (
    CreateOrderRequest,
    CreateOrderResponse,
    UpdateOrderStatusRequest,
    UpdateOrderStatusResponse,
)

router = APIRouter(prefix="/oracle", tags=["Oracle"])
logger = logging.getLogger(__name__)


@router.post("/orders", response_model=CreateOrderResponse)
def create_order(
    req: CreateOrderRequest,
    db: Session = Depends(get_db),
) -> CreateOrderResponse:
    """
    Create a new order in ORDERS for testing SSE change stream.

    Uses ORM for type-safe data insertion.

    Uses FastAPI Dependency Injection for automatic session management:
    - Auto-commit on success
    - Auto-rollback on error
    - Auto-cleanup

    Args:
        req: Order creation request
        db: Database session (injected)

    Returns:
        CreateOrderResponse with created order details

    Raises:
        HTTPException: On database errors
    """
    try:
        # Get next ID using ORM query builder
        max_id_stmt = select(func.coalesce(func.max(Order.order_id), 0))
        max_id = db.scalar(max_id_stmt)
        next_id = int(max_id) + 1

        # Create new order using ORM
        new_order = Order(
            order_id=next_id,
            customer_id=req.customer_id,
            status=req.status,
            salesman_id=req.salesman_id,
            order_date=datetime.now(),
        )

        db.add(new_order)
        db.flush()  # Flush to get any DB-generated values

        logger.info(f"Created order {new_order.order_id} for customer {new_order.customer_id}")

        return CreateOrderResponse(
            ok=True,
            order_id=new_order.order_id,
            customer_id=new_order.customer_id,
            status=new_order.status,
            salesman_id=new_order.salesman_id,
            order_date=new_order.order_date.isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to create order: {e}", exc_info=True)
        raise handle_db_error(e) from e


@router.patch("/orders/{order_id}/status", response_model=UpdateOrderStatusResponse)
def update_order_status(
    order_id: int,
    req: UpdateOrderStatusRequest,
    db: Session = Depends(get_db),
) -> UpdateOrderStatusResponse:
    """
    Update ORDERS.STATUS for testing SSE change stream.

    Uses ORM for type-safe query and update.

    Uses FastAPI Dependency Injection for automatic session management.

    Args:
        order_id: ID of the order to update
        req: Status update request
        db: Database session (injected)

    Returns:
        UpdateOrderStatusResponse with old and new status

    Raises:
        HTTPException: If order not found or database error occurs
    """
    try:
        # Query order using ORM
        stmt = select(Order).where(Order.order_id == order_id)
        order = db.scalar(stmt)

        if not order:
            logger.warning(f"Order {order_id} not found for status update")
            raise RecordNotFoundError("Order not found")

        # Store old status
        old_status = order.status

        # Update status using ORM
        order.status = req.status
        db.flush()

        logger.info(
            f"Updated order {order_id} status: {old_status} -> {req.status}"
        )

        return UpdateOrderStatusResponse(
            ok=True,
            order_id=order_id,
            old_status=old_status,
            new_status=req.status,
        )
    except RecordNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to update order {order_id} status: {e}", exc_info=True)
        raise handle_db_error(e) from e

"""
SQLAlchemy ORM models for database tables.

Uses SQLAlchemy 2.0 style with Mapped and mapped_column.
For complex queries, raw SQL can still be used via text().
"""

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Order(Base):
    """
    Order table model.

    Represents orders in the system for tracking and SSE streaming.
    """

    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    salesman_id: Mapped[int | None] = mapped_column(nullable=True)
    order_date: Mapped[datetime] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return (
            f"Order(order_id={self.order_id}, "
            f"customer_id={self.customer_id}, "
            f"status='{self.status}')"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "status": self.status,
            "salesman_id": self.salesman_id,
            "order_date": self.order_date.isoformat() if self.order_date else None,
        }

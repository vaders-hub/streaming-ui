"""
Custom exceptions and error handlers for the application.
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import (
    DBAPIError,
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
)


class DatabaseError(HTTPException):
    """Base database error"""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class RecordNotFoundError(HTTPException):
    """Record not found in database"""

    def __init__(self, detail: str = "Record not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class DuplicateRecordError(HTTPException):
    """Duplicate record violation"""

    def __init__(self, detail: str = "Duplicate record"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


def handle_db_error(error: Exception) -> HTTPException:
    """
    Convert SQLAlchemy exceptions to appropriate HTTP exceptions.

    Args:
        error: The exception to handle

    Returns:
        HTTPException with appropriate status code and message
    """
    # Integrity constraint violations (unique, foreign key, etc.)
    if isinstance(error, IntegrityError):
        return DuplicateRecordError(detail=f"Database constraint violation: {str(error.orig)}")

    # Operational errors (connection, transaction, etc.)
    if isinstance(error, OperationalError):
        return DatabaseError(detail=f"Database operation failed: {str(error.orig)}")

    # DBAPI errors (driver-level errors)
    if isinstance(error, DBAPIError):
        return DatabaseError(detail=f"Database API error: {str(error.orig)}")

    # Generic SQLAlchemy errors
    if isinstance(error, SQLAlchemyError):
        return DatabaseError(detail=f"Database error: {str(error)}")

    # Re-raise HTTPException as-is
    if isinstance(error, HTTPException):
        return error

    # Unknown errors
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unexpected error: {str(error)}",
    )

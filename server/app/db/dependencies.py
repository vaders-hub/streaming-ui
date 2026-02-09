"""
FastAPI dependencies for database session management.

Usage:
    @router.get("/items")
    def get_items(db: Session = Depends(get_db)):
        return db.execute(text("SELECT * FROM items")).fetchall()
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.connection import oracle_db


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for SQLAlchemy database sessions.

    Provides:
    - Automatic session creation
    - Automatic commit on success
    - Automatic rollback on error
    - Automatic session cleanup

    Usage:
        from fastapi import Depends
        from app.db.dependencies import get_db

        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            result = db.execute(text("SELECT * FROM users"))
            return result.fetchall()
    """
    db = oracle_db.get_session()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_readonly() -> Generator[Session, None, None]:
    """
    FastAPI dependency for read-only database sessions.

    No commit is performed, only cleanup.
    Use for SELECT queries to avoid unnecessary commits.

    Usage:
        @app.get("/stats")
        def get_stats(db: Session = Depends(get_db_readonly)):
            return db.execute(text("SELECT COUNT(*) FROM orders")).scalar()
    """
    db = oracle_db.get_session()
    try:
        yield db
    finally:
        db.close()

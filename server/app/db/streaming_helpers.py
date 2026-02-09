"""
Streaming-specific database helpers.

Provides session factory for SSE streaming endpoints.
"""

from collections.abc import Callable, Generator

from sqlalchemy.orm import Session

from app.db.connection import oracle_db


def get_session_factory() -> Callable[[], Generator[Session, None, None]]:
    """
    FastAPI dependency that provides a session factory for streaming functions.

    Returns a callable that creates new sessions with context manager support.
    This allows streaming functions to manage their own sessions per iteration.

    Usage in streaming functions:
        async def my_stream(
            session_factory=Depends(get_session_factory)
        ) -> AsyncGenerator[dict[str, str], None]:
            while True:
                with session_factory() as session:
                    result = session.execute(text("SELECT ..."))
                    yield {...}
                await asyncio.sleep(1)

    Usage in routers:
        @router.get("/stream/data")
        async def stream_data(session_factory=Depends(get_session_factory)):
            return EventSourceResponse(stream_my_data(session_factory))
    """
    return oracle_db.session_scope

from fastapi import FastAPI
# Force reload

from app.api.routers import (
    chat_router,
    health_router,
    oracle_router,
    redis_router,
    stream_router,
)


def include_routers(app: FastAPI):
    """Register all application routers"""
    app.include_router(health_router)
    app.include_router(stream_router)
    app.include_router(redis_router)
    app.include_router(chat_router)
    app.include_router(oracle_router)

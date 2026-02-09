import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.connection import oracle_db, redis_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting up...")
    try:
        oracle_db.connect()
    except Exception as e:
        logger.warning(f"Warning: Could not connect to Oracle: {e}")

    try:
        redis_db.connect()
    except Exception as e:
        logger.warning(f"Warning: Could not connect to Redis: {e}")

    yield

    # Shutdown
    logger.info("Shutting down...")
    oracle_db.disconnect()
    redis_db.disconnect()

import logging

# Force reload
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import include_routers
from app.core.config import settings
from app.core.lifespan import lifespan
from app.core.logging import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


# Create application
app = FastAPI(
    title="SSE Streaming Server",
    description="FastAPI server with SSE, Oracle, and Redis support",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
include_routers(app)


def main():
    """Entry point for the server"""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()

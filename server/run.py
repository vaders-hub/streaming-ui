import uvicorn
from app.core.config import settings

# Version 1.0.1

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )

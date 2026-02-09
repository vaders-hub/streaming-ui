import logging

def setup_logging(level: int = logging.INFO):
    """Configure basic logging for the application"""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Set third-party loggers to warning to reduce noise if needed
    # logging.getLogger("uvicorn").setLevel(logging.WARNING)

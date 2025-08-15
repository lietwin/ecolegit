"""Logging configuration."""

import logging
import sys
from typing import Optional

from ..config.constants import Environment


def setup_logging(
    environment: Environment = Environment.DEVELOPMENT,
    log_level: Optional[str] = None
) -> None:
    """Setup application logging configuration with error handling."""
    
    try:
        # Determine log level
        if log_level:
            level = getattr(logging, log_level.upper(), logging.INFO)
        elif environment == Environment.PRODUCTION:
            level = logging.WARNING
        elif environment == Environment.TESTING:
            level = logging.ERROR
        else:  # Development
            level = logging.DEBUG

        # Configure root logger
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Set specific logger levels
        logging.getLogger("uvicorn").setLevel(logging.INFO)
        logging.getLogger("fastapi").setLevel(logging.INFO)
        
        # Reduce noise from external libraries
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

        logger = logging.getLogger(__name__)
        logger.info(f"Logging configured for {environment} environment at {level} level")
        
    except Exception as e:
        # Fallback to basic logging if setup fails
        print(f"Warning: Logging setup failed ({e}), using basic configuration")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
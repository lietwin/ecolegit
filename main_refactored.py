"""Refactored main application entry point."""

import uvicorn
import logging
from src.application import create_app
from src.config.settings import ConfigLoader
from src.config.constants import Environment

logger = logging.getLogger(__name__)

# Create app instance for ASGI servers
app = create_app()


def main() -> None:
    """Main application entry point."""
    try:
        # Load configuration to get server settings
        config_loader = ConfigLoader()
        config = config_loader.load()
        
        # For Render deployment, we need to export the app
        global app
        app = create_app()
        
        # Run server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=config.port,
            reload=config.environment != Environment.PRODUCTION,
            log_level="info" if config.environment == Environment.PRODUCTION else "debug"
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


if __name__ == "__main__":
    main()
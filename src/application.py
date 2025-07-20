"""Application factory for creating FastAPI app."""

import logging
from fastapi import FastAPI

from .config.settings import AppConfig, ConfigLoader
from .config.constants import Environment
from .infrastructure.logging import setup_logging
from .api.dependencies import initialize_dependencies
from .api.middleware import setup_middleware, setup_rate_limiting
from .api.routes.calculation import create_calculation_router
from .api.routes.health import router as health_router, create_test_router

logger = logging.getLogger(__name__)


class ApplicationFactory:
    """Factory for creating and configuring FastAPI application."""

    @staticmethod
    def create_app(config_file: str = "config.json") -> FastAPI:
        """Create and configure FastAPI application."""
        
        # Load configuration
        config_loader = ConfigLoader(config_file)
        config = config_loader.load()
        
        # Setup logging
        setup_logging(config.environment)
        logger.info(f"Starting application in {config.environment} environment")
        
        # Initialize dependencies
        initialize_dependencies(config)
        
        # Create FastAPI app
        app = ApplicationFactory._create_fastapi_app(config)
        
        # Setup middleware
        setup_middleware(app, config)
        limiter = setup_rate_limiting(app, config)
        
        # Register routes
        ApplicationFactory._register_routes(app, config, limiter)
        
        logger.info("Application created and configured successfully")
        return app

    @staticmethod
    def _create_fastapi_app(config: AppConfig) -> FastAPI:
        """Create FastAPI application with proper configuration."""
        # Disable docs in production
        docs_url = "/docs" if config.environment != Environment.PRODUCTION else None
        redoc_url = "/redoc" if config.environment != Environment.PRODUCTION else None
        
        app = FastAPI(
            title="EcoLogits Webhook",
            version="1.0.0",
            description="Environmental impact calculation service for AI models",
            docs_url=docs_url,
            redoc_url=redoc_url
        )
        
        return app

    @staticmethod
    def _register_routes(app: FastAPI, config: AppConfig, limiter) -> None:
        """Register all application routes."""
        
        # Health and info routes (no rate limiting)
        app.include_router(health_router, tags=["health"])
        
        # Calculation routes (with rate limiting)
        calculation_router = create_calculation_router(limiter)
        app.include_router(calculation_router, tags=["calculation"])
        
        # Test routes (only in non-production)
        if config.environment != Environment.PRODUCTION:
            test_router = create_test_router()
            app.include_router(test_router, tags=["testing"])
            logger.info("Test endpoints enabled for non-production environment")
        else:
            logger.info("Test endpoints disabled for production environment")


def create_app(config_file: str = "config.json") -> FastAPI:
    """Convenience function to create FastAPI application."""
    return ApplicationFactory.create_app(config_file)
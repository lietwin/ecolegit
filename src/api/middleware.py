"""API middleware configuration."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ..config.settings import AppConfig

logger = logging.getLogger(__name__)


def setup_middleware(app: FastAPI, config: AppConfig) -> None:
    """Setup application middleware."""
    
    # Trusted Host Middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=config.security.trusted_hosts
    )
    logger.info(f"Trusted hosts configured: {config.security.trusted_hosts}")

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allowed_origins,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allowed_methods,
        allow_headers=config.cors.allowed_headers,
    )
    logger.info(f"CORS configured with origins: {config.cors.allowed_origins}")


def setup_rate_limiting(app: FastAPI, config: AppConfig) -> Limiter:
    """Setup rate limiting for the application."""
    if not config.rate_limiting.enabled:
        logger.info("Rate limiting disabled")
        return None
    
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    logger.info(f"Rate limiting configured: {config.rate_limiting.requests_per_minute} requests/minute")
    return limiter
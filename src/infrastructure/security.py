"""Simplified security implementation."""

import hashlib
import hmac
import logging
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from ..config.constants import HTTPStatus, HeaderNames, ErrorMessages
from ..config.settings import AppConfig

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Security related errors."""
    pass


def verify_api_key(config: AppConfig, credentials: Optional[HTTPAuthorizationCredentials]) -> bool:
    """Verify API key credentials."""
    if not config.security.enable_auth:
        return True

    if not credentials:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=ErrorMessages.API_KEY_REQUIRED
        )

    if not config.api_key:
        logger.error("API key not configured but authentication is enabled")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=ErrorMessages.API_KEY_NOT_CONFIGURED
        )

    if not hmac.compare_digest(credentials.credentials, config.api_key):
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=ErrorMessages.INVALID_API_KEY
        )

    logger.debug("API key authentication successful")
    return True


def verify_webhook_signature(config: AppConfig, request: Request, body: bytes) -> bool:
    """Verify HMAC-SHA256 webhook signature."""
    if not config.security.enable_webhook_signature:
        return True

    signature_header = request.headers.get(HeaderNames.WEBHOOK_SIGNATURE)
    if not signature_header:
        logger.warning("Missing webhook signature header")
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=ErrorMessages.WEBHOOK_SIGNATURE_REQUIRED
        )

    if not config.webhook_secret:
        logger.error("Webhook secret not configured but signature verification is enabled")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=ErrorMessages.WEBHOOK_SECRET_NOT_CONFIGURED
        )

    # Calculate expected signature
    expected_signature = hmac.new(
        config.webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    expected_header = f"sha256={expected_signature}"

    if not hmac.compare_digest(expected_header, signature_header):
        logger.warning("Invalid webhook signature")
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=ErrorMessages.INVALID_WEBHOOK_SIGNATURE
        )

    logger.debug("Webhook signature verification successful")
    return True


class SecurityManager:
    """Simplified security manager."""

    def __init__(self, config: AppConfig):
        self._config = config

    def verify_authentication(self, credentials: Optional[HTTPAuthorizationCredentials]) -> bool:
        """Verify authentication credentials."""
        return verify_api_key(self._config, credentials)

    def verify_webhook_signature(self, request: Request, body: bytes) -> bool:
        """Verify webhook signature."""
        return verify_webhook_signature(self._config, request, body)


def create_security_manager(config: AppConfig) -> SecurityManager:
    """Create security manager."""
    return SecurityManager(config)
"""Security infrastructure implementation."""

import hashlib
import hmac
import logging
from abc import ABC, abstractmethod
from typing import Protocol, Optional

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from ..config.constants import HTTPStatus, HeaderNames, ErrorMessages
from ..config.settings import AppConfig

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Security related errors."""
    pass


class AuthenticationService(ABC):
    """Abstract authentication service."""
    
    @abstractmethod
    def verify_credentials(self, credentials: Optional[HTTPAuthorizationCredentials]) -> bool:
        """Verify authentication credentials."""
        pass


class WebhookSignatureService(ABC):
    """Abstract webhook signature verification service."""
    
    @abstractmethod
    def verify_signature(self, request: Request, body: bytes) -> bool:
        """Verify webhook signature."""
        pass


class APIKeyAuthenticationService(AuthenticationService):
    """API key based authentication service."""

    def __init__(self, config: AppConfig):
        self._config = config

    def verify_credentials(self, credentials: Optional[HTTPAuthorizationCredentials]) -> bool:
        """Verify API key credentials."""
        if not self._config.security.enable_auth:
            return True

        if not credentials:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail=ErrorMessages.API_KEY_REQUIRED
            )

        if not self._config.api_key:
            logger.error("API key not configured but authentication is enabled")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=ErrorMessages.API_KEY_NOT_CONFIGURED
            )

        if not hmac.compare_digest(credentials.credentials, self._config.api_key):
            logger.warning("Invalid API key attempt")
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail=ErrorMessages.INVALID_API_KEY
            )

        logger.debug("API key authentication successful")
        return True


class HMACWebhookSignatureService(WebhookSignatureService):
    """HMAC-SHA256 webhook signature verification service."""

    def __init__(self, config: AppConfig):
        self._config = config

    def verify_signature(self, request: Request, body: bytes) -> bool:
        """Verify HMAC-SHA256 webhook signature."""
        if not self._config.security.enable_webhook_signature:
            return True

        signature_header = request.headers.get(HeaderNames.WEBHOOK_SIGNATURE)
        if not signature_header:
            logger.warning("Missing webhook signature header")
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail=ErrorMessages.WEBHOOK_SIGNATURE_REQUIRED
            )

        if not self._config.webhook_secret:
            logger.error("Webhook secret not configured but signature verification is enabled")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=ErrorMessages.WEBHOOK_SECRET_NOT_CONFIGURED
            )

        # Calculate expected signature
        expected_signature = hmac.new(
            self._config.webhook_secret.encode(),
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
    """Centralized security management."""

    def __init__(
        self,
        auth_service: AuthenticationService,
        webhook_service: WebhookSignatureService
    ):
        self._auth_service = auth_service
        self._webhook_service = webhook_service

    def verify_authentication(self, credentials: Optional[HTTPAuthorizationCredentials]) -> bool:
        """Verify authentication credentials."""
        return self._auth_service.verify_credentials(credentials)

    def verify_webhook_signature(self, request: Request, body: bytes) -> bool:
        """Verify webhook signature."""
        return self._webhook_service.verify_signature(request, body)


class SecurityFactory:
    """Factory for creating security services."""

    @staticmethod
    def create_security_manager(config: AppConfig) -> SecurityManager:
        """Create security manager with appropriate services."""
        auth_service = APIKeyAuthenticationService(config)
        webhook_service = HMACWebhookSignatureService(config)
        
        return SecurityManager(auth_service, webhook_service)
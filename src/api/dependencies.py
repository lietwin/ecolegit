"""FastAPI dependency injection setup."""

import logging
from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..config.settings import AppConfig
from ..domain.services import (
    ImpactCalculationService,
    CalculationIdService,
    HealthService,
    ModelInfoService,
    TestService
)
from ..infrastructure.security import SecurityManager, create_security_manager
from ..infrastructure.ecologits_adapter import EcologitsAdapter

logger = logging.getLogger(__name__)


class DependencyContainer:
    """Dependency injection container."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.security_manager = create_security_manager(config)
        self.ecologits_adapter = EcologitsAdapter()
        
        # Initialize services
        self.impact_service = ImpactCalculationService(self.ecologits_adapter, config)
        self.calculation_id_service = CalculationIdService()
        self.health_service = HealthService()
        self.model_info_service = ModelInfoService(self.ecologits_adapter, config)
        self.test_service = TestService(self.impact_service)
        
        logger.info("Dependencies initialized successfully")


# Container instance (initialized by application factory)
_container: DependencyContainer = None


def initialize_dependencies(config: AppConfig) -> None:
    """Initialize dependency container."""
    global _container
    _container = DependencyContainer(config)


def get_app_config() -> AppConfig:
    """Get application configuration."""
    if _container is None:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _container.config


def get_security_manager() -> SecurityManager:
    """Get security manager."""
    if _container is None:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _container.security_manager


def get_impact_calculation_service() -> ImpactCalculationService:
    """Get impact calculation service."""
    if _container is None:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _container.impact_service


def get_calculation_id_service() -> CalculationIdService:
    """Get calculation ID service."""
    if _container is None:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _container.calculation_id_service


def get_health_service() -> HealthService:
    """Get health service."""
    if _container is None:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _container.health_service


def get_model_info_service() -> ModelInfoService:
    """Get model info service."""
    if _container is None:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _container.model_info_service


def get_test_service() -> TestService:
    """Get test service."""
    if _container is None:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _container.test_service


# FastAPI security dependency
security = HTTPBearer(auto_error=False)


def verify_authentication(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    security_manager: Annotated[SecurityManager, Depends(get_security_manager)]
) -> bool:
    """Verify authentication credentials."""
    return security_manager.verify_authentication(credentials)


# Type aliases for cleaner dependency injection
AppConfigDep = Annotated[AppConfig, Depends(get_app_config)]
SecurityManagerDep = Annotated[SecurityManager, Depends(get_security_manager)]
ImpactCalculationServiceDep = Annotated[ImpactCalculationService, Depends(get_impact_calculation_service)]
CalculationIdServiceDep = Annotated[CalculationIdService, Depends(get_calculation_id_service)]
HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
ModelInfoServiceDep = Annotated[ModelInfoService, Depends(get_model_info_service)]
TestServiceDep = Annotated[TestService, Depends(get_test_service)]
AuthenticatedDep = Annotated[bool, Depends(verify_authentication)]
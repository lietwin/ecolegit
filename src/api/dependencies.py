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
from ..infrastructure.security import SecurityManager, SecurityFactory
from ..infrastructure.ecologits_adapter import EcologitsAdapter

logger = logging.getLogger(__name__)


# Global dependency instances (initialized by application factory)
_app_config: AppConfig = None
_security_manager: SecurityManager = None
_ecologits_adapter: EcologitsAdapter = None
_services: dict = {}


def initialize_dependencies(config: AppConfig) -> None:
    """Initialize global dependencies."""
    global _app_config, _security_manager, _ecologits_adapter, _services
    
    _app_config = config
    _security_manager = SecurityFactory.create_security_manager(config)
    _ecologits_adapter = EcologitsAdapter()
    
    # Initialize services
    impact_service = ImpactCalculationService(_ecologits_adapter, config)
    
    _services = {
        'impact_calculation': impact_service,
        'calculation_id': CalculationIdService(),
        'health': HealthService(),
        'model_info': ModelInfoService(_ecologits_adapter, config),
        'test': TestService(impact_service)
    }
    
    logger.info("Dependencies initialized successfully")


def get_app_config() -> AppConfig:
    """Get application configuration."""
    if _app_config is None:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _app_config


def get_security_manager() -> SecurityManager:
    """Get security manager."""
    if _security_manager is None:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _security_manager


def get_impact_calculation_service() -> ImpactCalculationService:
    """Get impact calculation service."""
    if 'impact_calculation' not in _services:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _services['impact_calculation']


def get_calculation_id_service() -> CalculationIdService:
    """Get calculation ID service."""
    if 'calculation_id' not in _services:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _services['calculation_id']


def get_health_service() -> HealthService:
    """Get health service."""
    if 'health' not in _services:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _services['health']


def get_model_info_service() -> ModelInfoService:
    """Get model info service."""
    if 'model_info' not in _services:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _services['model_info']


def get_test_service() -> TestService:
    """Get test service."""
    if 'test' not in _services:
        raise RuntimeError("Dependencies not initialized. Call initialize_dependencies() first.")
    return _services['test']


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
"""Health and info API endpoints."""

import logging
from fastapi import APIRouter

from ...domain.models import HealthStatus, ModelInfo, TestResult
from ...config.constants import Environment
from ..dependencies import (
    AppConfigDep,
    HealthServiceDep,
    ModelInfoServiceDep,
    TestServiceDep
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(
    health_service: HealthServiceDep
) -> dict:
    """Health check endpoint."""
    logger.debug("Health check requested")
    status = health_service.get_health_status()
    
    # Check EcoLogits availability
    try:
        from ecologits.impacts import Impacts
        from ecologits.model_repository import models
        ecologits_status = "available"
        model_count = len(models)
    except ImportError as e:
        ecologits_status = f"unavailable: {e}"
        model_count = 0
    
    return {
        "status": status.status,
        "service": status.service,
        "timestamp": status.timestamp,
        "dependencies": {
            "ecologits": ecologits_status,
            "available_models": model_count
        }
    }


@router.get("/models")
async def get_supported_models(
    model_info_service: ModelInfoServiceDep
) -> dict:
    """Get list of supported models."""
    logger.debug("Supported models requested")
    info = model_info_service.get_model_info()
    
    return {
        "supported_models": info.supported_models,
        "total_ecologits_models": info.total_ecologits_models
    }


def create_test_router() -> APIRouter:
    """Create test router that's only available in non-production environments."""
    test_router = APIRouter()
    
    @test_router.get("/test")
    async def test_calculation(
        config: AppConfigDep,
        test_service: TestServiceDep
    ) -> dict:
        """Test calculation endpoint (development/testing only)."""
        if config.environment == Environment.PRODUCTION:
            # This endpoint should not be registered in production
            # But as a safety check, we include this
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")
        
        logger.info("Test calculation requested")
        result = test_service.run_test_calculation(config.environment.value)
        
        return {
            "test_model": result.test_model,
            "test_tokens": result.test_tokens,
            "energy_kwh": result.energy_kwh,
            "gwp_kgco2eq": result.gwp_kgco2eq,
            "success": result.success,
            "environment": result.environment
        }
    
    return test_router
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
        from ecologits.model_repository import models
        ecologits_status = "available"
        
        # Get model count using simplified approach
        try:
            model_list = models.list_models()
            model_count = len(model_list)
        except Exception:
            model_count = 0
            
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


@router.get("/debug/models")
async def debug_models_structure():
    """Debug endpoint to inspect EcoLogits models structure (non-production only)."""
    try:
        from ecologits.model_repository import models
        
        model_info = {
            "type": str(type(models)),
            "attributes": [attr for attr in dir(models) if not attr.startswith('_')],
            "has_models_attr": hasattr(models, 'models'),
            "has_private_models_attr": hasattr(models, '_models'),
            "has_get_method": hasattr(models, 'get'),
            "has_keys_method": hasattr(models, 'keys'),
            "is_dict_like": hasattr(models, '__getitem__'),
        }
        
        # Try to get a few sample models
        sample_models = {}
        for attr in model_info["attributes"][:5]:  # Just first 5
            try:
                sample_models[attr] = str(type(getattr(models, attr)))
            except:
                pass
                
        return {
            "model_repository_info": model_info,
            "sample_models": sample_models
        }
    except ImportError as e:
        return {"error": f"EcoLogits not available: {e}"}


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
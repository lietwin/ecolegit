"""Model registry and discovery API endpoints."""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...domain.model_discovery import ModelDiscoveryService, ModelMatch
from ..dependencies import ModelDiscoveryServiceDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["models"])


class ModelSearchRequest(BaseModel):
    """Request model for model search."""
    query: str
    limit: Optional[int] = 10


class ModelSearchResult(BaseModel):
    """Search result for model lookup."""
    name: str
    confidence: float


class ModelMatchResult(BaseModel):
    """Result of model matching."""
    matched_name: str
    original_name: str
    confidence: float
    match_type: str
    available: bool


class SupportedModelsResponse(BaseModel):
    """Response for supported models."""
    models: List[str]
    total_count: int
    by_provider: Dict[str, List[str]]
    cache_age_seconds: Optional[int] = None


@router.get("/supported", response_model=SupportedModelsResponse)
async def get_supported_models(
    model_discovery: ModelDiscoveryServiceDep
) -> SupportedModelsResponse:
    """Get all models supported by EcoLogits."""
    try:
        models = model_discovery.get_supported_models()
        by_provider = model_discovery.get_models_by_provider()
        
        return SupportedModelsResponse(
            models=models,
            total_count=len(models),
            by_provider=by_provider
        )
    except Exception as e:
        logger.error(f"Error getting supported models: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve supported models")


@router.get("/search")
async def search_models(
    model_discovery: ModelDiscoveryServiceDep,
    q: str = Query(..., description="Search query for model names"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
) -> List[ModelSearchResult]:
    """Search for models by name or partial name."""
    try:
        results = model_discovery.search_models(q, limit)
        
        return [
            ModelSearchResult(name=name, confidence=confidence)
            for name, confidence in results
        ]
    except Exception as e:
        logger.error(f"Error searching models with query '{q}': {e}")
        raise HTTPException(status_code=500, detail="Failed to search models")


@router.get("/match")
async def match_model(
    model_discovery: ModelDiscoveryServiceDep,
    name: str = Query(..., description="Model name to match")
) -> ModelMatchResult:
    """Find the best matching model for a given name."""
    try:
        match = model_discovery.find_best_match(name)
        
        if not match:
            raise HTTPException(
                status_code=404, 
                detail=f"No suitable model found for '{name}'. Use /models/search to find similar models."
            )
        
        return ModelMatchResult(
            matched_name=match.matched_name,
            original_name=match.original_name,
            confidence=match.confidence,
            match_type=match.match_type,
            available=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching model '{name}': {e}")
        raise HTTPException(status_code=500, detail="Failed to match model")


@router.post("/refresh")
async def refresh_model_cache(
    model_discovery: ModelDiscoveryServiceDep
) -> Dict[str, Any]:
    """Force refresh of the model cache from EcoLogits."""
    try:
        models = model_discovery.refresh_cache()
        
        return {
            "message": "Model cache refreshed successfully",
            "discovered_models": len(models),
            "models": list(models.keys())[:20]  # Show first 20 for brevity
        }
    except Exception as e:
        logger.error(f"Error refreshing model cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh model cache")


@router.get("/providers")
async def get_providers(
    model_discovery: ModelDiscoveryServiceDep
) -> Dict[str, Dict[str, Any]]:
    """Get information about supported providers."""
    try:
        by_provider = model_discovery.get_models_by_provider()
        
        provider_info = {}
        for provider, models in by_provider.items():
            provider_info[provider] = {
                "name": provider,
                "model_count": len(models),
                "models": models
            }
        
        return provider_info
    except Exception as e:
        logger.error(f"Error getting provider information: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider information")


@router.get("/validate/{model_name}")
async def validate_model(
    model_name: str,
    model_discovery: ModelDiscoveryServiceDep
) -> Dict[str, Any]:
    """Validate if a model name is supported and get suggestions if not."""
    try:
        match = model_discovery.find_best_match(model_name)
        
        if match and match.confidence >= 0.9:
            return {
                "valid": True,
                "model_name": model_name,
                "matched_name": match.matched_name,
                "confidence": match.confidence,
                "match_type": match.match_type
            }
        else:
            # Get suggestions
            suggestions = model_discovery.search_models(model_name, 5)
            
            return {
                "valid": False,
                "model_name": model_name,
                "suggestions": [
                    {"name": name, "confidence": conf} 
                    for name, conf in suggestions
                ],
                "message": f"Model '{model_name}' not found. Consider using one of the suggestions."
            }
    except Exception as e:
        logger.error(f"Error validating model '{model_name}': {e}")
        raise HTTPException(status_code=500, detail="Failed to validate model")
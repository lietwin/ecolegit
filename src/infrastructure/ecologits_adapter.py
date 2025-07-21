"""Ecologits external service adapter."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

try:
    from ecologits.impacts import Impacts
    from ecologits.model_repository import models
    ECOLOGITS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"EcoLogits not available: {e}")
    ECOLOGITS_AVAILABLE = False
    Impacts = None
    models = {}

from ..domain.services import EcologitsRepository


class EcologitsServiceError(Exception):
    """Ecologits service related errors."""
    pass


class EcologitsAdapter(EcologitsRepository):
    """Adapter for ecologits external service."""

    def __init__(self):
        """Initialize the ecologits adapter."""
        if not ECOLOGITS_AVAILABLE:
            raise EcologitsServiceError("EcoLogits library is not installed or available")
        self._models = models
        logger.info("EcologitsAdapter initialized")
    
    def _get_provider_from_model_name(self, model_name: str) -> str:
        """Detect provider from model name patterns."""
        model_lower = model_name.lower()
        
        if model_lower.startswith("gpt-") or "gpt" in model_lower:
            return "openai"
        elif model_lower.startswith("claude-") or "claude" in model_lower:
            return "anthropic"
        elif model_lower.startswith("gemini-") or "gemini" in model_lower:
            return "google"
        else:
            # Default fallback - try openai first as most common
            return "openai"

    def get_model(self, model_name: str) -> object:
        """Get model by name from ecologits repository."""
        try:
            # Use the correct EcoLogits API - find_model method with provider
            provider = self._get_provider_from_model_name(model_name)
            model = self._models.find_model(provider, model_name)
            
            if model is None:
                raise EcologitsServiceError(f"Model '{model_name}' not found in ecologits repository")
            
            logger.debug(f"Successfully found model '{model_name}': {model.name} ({model.provider.value})")
            return model
        except Exception as e:
            logger.error(f"Error getting model '{model_name}': {e}")
            raise EcologitsServiceError(f"Failed to get model '{model_name}'") from e

    def calculate_impacts(self, model: object, input_tokens: int, output_tokens: int) -> object:
        """Calculate environmental impacts using ecologits simple approach."""
        try:
            from ecologits.tracers.utils import llm_impacts
            
            # Use the same simple approach as HuggingFace calculator
            # Get provider from model
            provider = model.provider.value  # e.g., "openai"
            model_name = model.name  # e.g., "gpt-4o"
            
            # Calculate impacts using llm_impacts function
            impacts = llm_impacts(
                provider=provider,
                model_name=model_name,
                output_token_count=output_tokens,
                request_latency=1.0  # Default latency in seconds
            )
            
            logger.debug(
                f"Impact calculation successful: "
                f"energy={impacts.energy.value}, gwp={impacts.gwp.value}"
            )
            
            return impacts
            
        except Exception as e:
            logger.error(f"Error calculating impacts: {e}")
            raise EcologitsServiceError("Failed to calculate environmental impacts") from e

    def get_available_models(self) -> Dict[str, object]:
        """Get all available models from ecologits repository."""
        try:
            # Use the correct EcoLogits API - list_models method
            model_list = self._models.list_models()
            
            # Convert list of Model objects to dictionary {name: model}
            model_dict = {}
            for model in model_list:
                model_dict[model.name] = model
            
            logger.debug(f"Retrieved {len(model_dict)} models from EcoLogits")
            return model_dict
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return {}

    def is_model_supported(self, model_name: str) -> bool:
        """Check if model is supported by ecologits."""
        try:
            # Use the correct EcoLogits API - try to find the model with provider
            provider = self._get_provider_from_model_name(model_name)
            model = self._models.find_model(provider, model_name)
            return model is not None
        except Exception:
            # If find_model fails, model is not supported
            return False
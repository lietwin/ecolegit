"""Ecologits external service adapter."""

import logging
from typing import Dict

from ecologits.impacts import Impacts
from ecologits.model_repository import models

from ..domain.services import EcologitsRepository

logger = logging.getLogger(__name__)


class EcologitsServiceError(Exception):
    """Ecologits service related errors."""
    pass


class EcologitsAdapter(EcologitsRepository):
    """Adapter for ecologits external service."""

    def __init__(self):
        """Initialize the ecologits adapter."""
        self._models = models
        logger.info("EcologitsAdapter initialized")

    def get_model(self, model_name: str) -> object:
        """Get model by name from ecologits repository."""
        try:
            if model_name not in self._models:
                raise EcologitsServiceError(f"Model '{model_name}' not found in ecologits repository")
            
            return self._models[model_name]
        except Exception as e:
            logger.error(f"Error getting model '{model_name}': {e}")
            raise EcologitsServiceError(f"Failed to get model '{model_name}'") from e

    def calculate_impacts(self, model: object, input_tokens: int, output_tokens: int) -> object:
        """Calculate environmental impacts using ecologits."""
        try:
            impacts = Impacts.from_model_and_tokens(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens
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
            return dict(self._models)
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            raise EcologitsServiceError("Failed to get available models") from e

    def is_model_supported(self, model_name: str) -> bool:
        """Check if model is supported by ecologits."""
        return model_name in self._models
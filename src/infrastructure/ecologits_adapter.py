"""Ecologits external service adapter."""

import logging
from typing import Dict

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

logger = logging.getLogger(__name__)


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

    def get_model(self, model_name: str) -> object:
        """Get model by name from ecologits repository."""
        try:
            # Try different ways to access the model
            if hasattr(self._models, 'get'):
                model = self._models.get(model_name)
            elif hasattr(self._models, model_name):
                model = getattr(self._models, model_name)
            else:
                # Try accessing through internal attributes
                if hasattr(self._models, '_models'):
                    model = self._models._models.get(model_name)
                elif hasattr(self._models, 'models'):
                    model = self._models.models.get(model_name)
                else:
                    model = None
            
            if model is None:
                raise EcologitsServiceError(f"Model '{model_name}' not found in ecologits repository")
            
            return model
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
            # ModelRepository is not directly iterable, need to access its models
            if hasattr(self._models, '_models') and hasattr(self._models._models, 'items'):
                return dict(self._models._models)
            elif hasattr(self._models, 'models') and hasattr(self._models.models, 'items'):
                return dict(self._models.models)
            else:
                # Iterate through attributes to find model objects
                model_dict = {}
                for attr_name in dir(self._models):
                    if not attr_name.startswith('_') and not attr_name.startswith('__'):
                        try:
                            attr_value = getattr(self._models, attr_name)
                            # Skip methods and properties
                            if not callable(attr_value) and not isinstance(attr_value, property):
                                model_dict[attr_name] = attr_value
                        except Exception:
                            continue
                return model_dict
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return {}

    def is_model_supported(self, model_name: str) -> bool:
        """Check if model is supported by ecologits."""
        try:
            # Check if model exists using getattr
            if hasattr(self._models, model_name):
                return getattr(self._models, model_name, None) is not None
            elif hasattr(self._models, '_models') and hasattr(self._models._models, '__contains__'):
                return model_name in self._models._models
            elif hasattr(self._models, 'models') and hasattr(self._models.models, '__contains__'):
                return model_name in self._models.models
            else:
                return False
        except Exception:
            return False
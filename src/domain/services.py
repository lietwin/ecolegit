"""Domain services for business logic."""

import hashlib
import time
import logging
from abc import ABC, abstractmethod
from typing import Protocol, Dict

from .models import CalculationResult, HealthStatus, ModelInfo, TestResult
from ..config.constants import ErrorMessages, SecurityConstants
from ..config.settings import AppConfig

logger = logging.getLogger(__name__)


class EcologitsRepository(Protocol):
    """Protocol for ecologits integration."""
    
    def get_model(self, model_name: str) -> object:
        """Get model by name."""
        ...
    
    def calculate_impacts(self, model: object, input_tokens: int, output_tokens: int) -> object:
        """Calculate environmental impacts."""
        ...
    
    def get_available_models(self) -> Dict[str, object]:
        """Get all available models."""
        ...
    
    def is_model_supported(self, model_name: str) -> bool:
        """Check if model is supported."""
        ...


class ImpactCalculationService:
    """Service for calculating environmental impact."""

    def __init__(self, ecologits_repo: EcologitsRepository, config: AppConfig, model_discovery_service=None):
        self._ecologits_repo = ecologits_repo
        self._config = config
        self._model_discovery_service = model_discovery_service

    def calculate_impact(self, model: str, input_tokens: int, output_tokens: int) -> CalculationResult:
        """Calculate environmental impact with proper error handling."""
        try:
            # Validate input
            if input_tokens < 0 or output_tokens < 0:
                return CalculationResult.error_result(ErrorMessages.TOKEN_COUNTS_NEGATIVE)

            # Normalize model name
            normalized_model = self._normalize_model(model)
            
            # Check if model is supported
            if not self._ecologits_repo.is_model_supported(normalized_model):
                error_msg = ErrorMessages.MODEL_NOT_SUPPORTED.format(model=normalized_model)
                return CalculationResult.error_result(error_msg)

            # Get model and calculate impacts
            ecologits_model = self._ecologits_repo.get_model(normalized_model)
            impacts = self._ecologits_repo.calculate_impacts(
                model=ecologits_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )

            return CalculationResult.success_result(
                energy_kwh=float(impacts.energy.value.mean),
                gwp_kgco2eq=float(impacts.gwp.value.mean),
                normalized_model=normalized_model
            )

        except Exception as e:
            logger.error(f"Calculation error for model {model}: {type(e).__name__}: {e}")
            # In development, show more details
            if normalized_model:
                error_detail = f"Calculation failed for {normalized_model}: {type(e).__name__}"
            else:
                error_detail = f"Model normalization failed: {type(e).__name__}"
            return CalculationResult.error_result(error_detail)

    def _normalize_model(self, model_name: str) -> str:
        """Normalize model name using dynamic model discovery or fallback to config mappings."""
        if self._model_discovery_service:
            # Use dynamic model discovery
            match = self._model_discovery_service.find_best_match(model_name)
            if match and match.confidence >= 0.6:  # Accept matches with 60%+ confidence
                logger.debug(f"Model '{model_name}' matched to '{match.matched_name}' via {match.match_type} (confidence: {match.confidence:.2f})")
                return match.matched_name
            else:
                # No good match found
                logger.warning(f"No suitable match found for model '{model_name}'")
                return model_name
        else:
            # Fallback to static mappings (for backwards compatibility)
            return self._config.model_mappings.get(model_name.lower(), model_name)


class CalculationIdService:
    """Service for generating secure calculation IDs."""

    @staticmethod
    def generate_id(model: str, input_tokens: int, output_tokens: int) -> str:
        """Generate secure calculation ID."""
        data = f"{model}-{input_tokens}-{output_tokens}-{time.time()}"
        calc_id = hashlib.sha256(data.encode()).hexdigest()[:SecurityConstants.CALCULATION_ID_LENGTH]
        return f"calc-{calc_id}"


class HealthService:
    """Service for health checks."""

    def __init__(self, service_name: str = "ecologits-webhook"):
        self._service_name = service_name

    def get_health_status(self) -> HealthStatus:
        """Get current health status."""
        return HealthStatus.healthy(self._service_name)


class ModelInfoService:
    """Service for model information."""

    def __init__(self, ecologits_repo: EcologitsRepository, config: AppConfig):
        self._ecologits_repo = ecologits_repo
        self._config = config

    def get_model_info(self) -> ModelInfo:
        """Get supported model information."""
        available_models = self._ecologits_repo.get_available_models()
        
        return ModelInfo(
            supported_models=list(self._config.model_mappings.keys()),
            total_ecologits_models=len(available_models)
        )


class TestService:
    """Service for test calculations."""

    def __init__(self, calculation_service: ImpactCalculationService):
        self._calculation_service = calculation_service

    def run_test_calculation(self, environment: str) -> TestResult:
        """Run a test calculation."""
        test_model = "gpt-4o"
        input_tokens = 1000
        output_tokens = 500
        
        result = self._calculation_service.calculate_impact(
            model=test_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        return TestResult(
            test_model=test_model,
            test_tokens=f"{input_tokens} input + {output_tokens} output",
            energy_kwh=result.energy_kwh,
            gwp_kgco2eq=result.gwp_kgco2eq,
            success=result.success,
            environment=environment
        )
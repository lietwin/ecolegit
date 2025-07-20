"""Domain models with proper validation."""

import json
from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field, field_validator

from ..config.constants import SecurityConstants, ErrorMessages


class UsageRequest(BaseModel):
    """Request model for environmental impact calculation."""
    
    model: str = Field(..., min_length=1, max_length=100)
    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    metadata: Optional[Dict] = Field(default=None, max_length=SecurityConstants.METADATA_MAX_ITEMS)
    
    model_config = {"validate_assignment": True}

    @field_validator('model')
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate and sanitize model name."""
        if not v.replace('-', '').replace('.', '').replace('_', '').isalnum():
            raise ValueError(ErrorMessages.MODEL_NAME_INVALID_CHARS)
        return v.strip().lower()

    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v: Optional[Dict]) -> Optional[Dict]:
        """Validate metadata size and content."""
        if v is None:
            return v
        
        # Check serialized size
        serialized = json.dumps(v)
        if len(serialized) > SecurityConstants.METADATA_SIZE_LIMIT_BYTES:
            raise ValueError(ErrorMessages.METADATA_TOO_LARGE)
        
        return v


class ImpactResponse(BaseModel):
    """Response model for environmental impact calculation."""
    
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    energy_kwh: float
    gwp_kgco2eq: float
    calculation_id: str
    timestamp: str
    success: bool
    error: Optional[str] = None


@dataclass
class CalculationResult:
    """Domain object for calculation results."""
    
    energy_kwh: float
    gwp_kgco2eq: float
    success: bool
    error: Optional[str] = None
    normalized_model: Optional[str] = None

    @classmethod
    def success_result(
        cls, 
        energy_kwh: float, 
        gwp_kgco2eq: float, 
        normalized_model: str
    ) -> "CalculationResult":
        """Create successful calculation result."""
        return cls(
            energy_kwh=energy_kwh,
            gwp_kgco2eq=gwp_kgco2eq,
            success=True,
            normalized_model=normalized_model
        )

    @classmethod
    def error_result(cls, error_message: str) -> "CalculationResult":
        """Create error calculation result."""
        return cls(
            energy_kwh=0.0,
            gwp_kgco2eq=0.0,
            success=False,
            error=error_message
        )


@dataclass
class HealthStatus:
    """Health check status."""
    
    status: str
    service: str
    timestamp: str

    @classmethod
    def healthy(cls, service_name: str) -> "HealthStatus":
        """Create healthy status."""
        return cls(
            status="healthy",
            service=service_name,
            timestamp=datetime.utcnow().isoformat()
        )


@dataclass
class ModelInfo:
    """Model information."""
    
    supported_models: list[str]
    total_ecologits_models: int


@dataclass
class TestResult:
    """Test calculation result."""
    
    test_model: str
    test_tokens: str
    energy_kwh: float
    gwp_kgco2eq: float
    success: bool
    environment: str
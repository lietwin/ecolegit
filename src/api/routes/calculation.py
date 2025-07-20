"""Calculation API endpoints."""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from slowapi import Limiter

from ...domain.models import UsageRequest, ImpactResponse
from ...config.constants import Environment
from ..dependencies import (
    AppConfigDep,
    SecurityManagerDep,
    ImpactCalculationServiceDep,
    CalculationIdServiceDep,
    AuthenticatedDep
)

logger = logging.getLogger(__name__)

router = APIRouter()


def create_calculation_router(limiter: Limiter = None) -> APIRouter:
    """Create calculation router with optional rate limiting."""
    
    if limiter:
        @router.post("/calculate", response_model=ImpactResponse)
        @limiter.limit("60/minute")  # Default rate limit, will be overridden by config
        async def calculate_environmental_impact(
            request: Request,
            usage_request: UsageRequest,
            config: AppConfigDep,
            security_manager: SecurityManagerDep,
            calculation_service: ImpactCalculationServiceDep,
            id_service: CalculationIdServiceDep,
            authenticated: AuthenticatedDep
        ) -> ImpactResponse:
            return await _calculate_environmental_impact(
                request, usage_request, config, security_manager,
                calculation_service, id_service, authenticated
            )
    else:
        @router.post("/calculate", response_model=ImpactResponse)
        async def calculate_environmental_impact(
            request: Request,
            usage_request: UsageRequest,
            config: AppConfigDep,
            security_manager: SecurityManagerDep,
            calculation_service: ImpactCalculationServiceDep,
            id_service: CalculationIdServiceDep,
            authenticated: AuthenticatedDep
        ) -> ImpactResponse:
            return await _calculate_environmental_impact(
                request, usage_request, config, security_manager,
                calculation_service, id_service, authenticated
            )
    
    return router


async def _calculate_environmental_impact(
    request: Request,
    usage_request: UsageRequest,
    config: AppConfigDep,
    security_manager: SecurityManagerDep,
    calculation_service: ImpactCalculationServiceDep,
    id_service: CalculationIdServiceDep,
    authenticated: AuthenticatedDep
) -> ImpactResponse:
    """
    Calculate environmental impact of AI model usage.
    
    Main webhook endpoint for Make.com integration.
    """
    logger.info(f"Calculation request for model: {usage_request.model}")
    
    # Verify webhook signature
    body = await request.body()
    security_manager.verify_webhook_signature(request, body)
    
    # Calculate environmental impact
    result = calculation_service.calculate_impact(
        model=usage_request.model,
        input_tokens=usage_request.input_tokens,
        output_tokens=usage_request.output_tokens
    )
    
    # Generate secure calculation ID
    calculation_id = id_service.generate_id(
        model=usage_request.model,
        input_tokens=usage_request.input_tokens,
        output_tokens=usage_request.output_tokens
    )
    
    # Create response
    response = ImpactResponse(
        model=usage_request.model,
        input_tokens=usage_request.input_tokens,
        output_tokens=usage_request.output_tokens,
        total_tokens=usage_request.input_tokens + usage_request.output_tokens,
        energy_kwh=result.energy_kwh,
        gwp_kgco2eq=result.gwp_kgco2eq,
        calculation_id=calculation_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        success=result.success,
        error=result.error
    )
    
    logger.info(f"Calculation completed: success={result.success}, id={calculation_id}")
    return response
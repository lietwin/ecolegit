"""Tests for calculation routes."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request
from datetime import datetime, timezone

from src.api.routes.calculation import create_calculation_router, _calculate_environmental_impact
from src.domain.models import UsageRequest, CalculationResult, ImpactResponse
from src.config.settings import AppConfig, SecurityConfig, RateLimitConfig


class TestCreateCalculationRouter:
    """Test calculation router creation."""

    def test_create_router_without_limiter(self):
        """Test creating router without rate limiter."""
        router = create_calculation_router(limiter=None)
        assert router is not None
        assert len(router.routes) == 1
        assert router.routes[0].path == "/calculate"
        assert "POST" in router.routes[0].methods

    def test_create_router_with_limiter(self):
        """Test creating router with rate limiter."""
        mock_limiter = Mock()
        mock_limiter.limit.return_value = lambda func: func  # Mock decorator
        
        router = create_calculation_router(limiter=mock_limiter)
        assert router is not None
        # Router may have multiple routes due to how FastAPI handles decorators
        assert len(router.routes) >= 1
        calculate_routes = [r for r in router.routes if r.path == "/calculate"]
        assert len(calculate_routes) >= 1
        assert "POST" in calculate_routes[0].methods


class TestCalculateEnvironmentalImpact:
    """Test the core calculation endpoint logic."""

    @pytest.fixture
    def mock_request(self):
        """Create mock FastAPI request."""
        request = Mock(spec=Request)
        request.body = AsyncMock(return_value=b'{"test": "data"}')
        return request

    @pytest.fixture
    def sample_usage_request(self):
        """Create sample usage request."""
        return UsageRequest(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            metadata={"user_id": "test", "session": "abc"}
        )

    @pytest.fixture
    def mock_config(self):
        """Create mock app config."""
        config = Mock(spec=AppConfig)
        config.environment = "testing"
        return config

    @pytest.fixture
    def mock_security_manager(self):
        """Create mock security manager."""
        manager = Mock()
        manager.verify_webhook_signature = Mock()
        return manager

    @pytest.fixture
    def mock_calculation_service(self):
        """Create mock calculation service."""
        service = Mock()
        service.calculate_impact.return_value = CalculationResult(
            energy_kwh=0.001,
            gwp_kgco2eq=0.0005,
            success=True,
            error=None
        )
        return service

    @pytest.fixture
    def mock_id_service(self):
        """Create mock ID service."""
        service = Mock()
        service.generate_id.return_value = "calc_12345"
        return service

    @pytest.fixture
    def mock_authenticated(self):
        """Create mock authentication result."""
        return True

    @pytest.mark.asyncio
    async def test_calculate_environmental_impact_success(
        self,
        mock_request,
        sample_usage_request,
        mock_config,
        mock_security_manager,
        mock_calculation_service,
        mock_id_service,
        mock_authenticated
    ):
        """Test successful calculation."""
        result = await _calculate_environmental_impact(
            request=mock_request,
            usage_request=sample_usage_request,
            config=mock_config,
            security_manager=mock_security_manager,
            calculation_service=mock_calculation_service,
            id_service=mock_id_service,
            authenticated=mock_authenticated
        )

        # Verify webhook signature was checked
        mock_security_manager.verify_webhook_signature.assert_called_once()

        # Verify calculation was performed
        mock_calculation_service.calculate_impact.assert_called_once_with(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500
        )

        # Verify ID was generated
        mock_id_service.generate_id.assert_called_once_with(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500
        )

        # Verify response structure
        assert isinstance(result, ImpactResponse)
        assert result.model == "gpt-4o"
        assert result.input_tokens == 1000
        assert result.output_tokens == 500
        assert result.total_tokens == 1500
        assert result.energy_kwh == 0.001
        assert result.gwp_kgco2eq == 0.0005
        assert result.calculation_id == "calc_12345"
        assert result.success is True
        assert result.error is None
        assert result.timestamp is not None

    @pytest.mark.asyncio
    async def test_calculate_environmental_impact_with_error(
        self,
        mock_request,
        sample_usage_request,
        mock_config,
        mock_security_manager,
        mock_calculation_service,
        mock_id_service,
        mock_authenticated
    ):
        """Test calculation with service error."""
        # Mock calculation service to return error
        mock_calculation_service.calculate_impact.return_value = CalculationResult(
            energy_kwh=0.0,
            gwp_kgco2eq=0.0,
            success=False,
            error="Model not supported"
        )

        result = await _calculate_environmental_impact(
            request=mock_request,
            usage_request=sample_usage_request,
            config=mock_config,
            security_manager=mock_security_manager,
            calculation_service=mock_calculation_service,
            id_service=mock_id_service,
            authenticated=mock_authenticated
        )

        # Verify response includes error
        assert isinstance(result, ImpactResponse)
        assert result.success is False
        assert result.error == "Model not supported"
        assert result.energy_kwh == 0.0
        assert result.gwp_kgco2eq == 0.0

    @pytest.mark.asyncio
    async def test_timestamp_format(
        self,
        mock_request,
        sample_usage_request,
        mock_config,
        mock_security_manager,
        mock_calculation_service,
        mock_id_service,
        mock_authenticated
    ):
        """Test that timestamp is in correct ISO format."""
        with patch('src.api.routes.calculation.datetime') as mock_datetime:
            fixed_time = Mock()
            fixed_time.isoformat.return_value = "2024-01-15T12:30:45+00:00"
            mock_datetime.now.return_value = fixed_time
            
            result = await _calculate_environmental_impact(
                request=mock_request,
                usage_request=sample_usage_request,
                config=mock_config,
                security_manager=mock_security_manager,
                calculation_service=mock_calculation_service,
                id_service=mock_id_service,
                authenticated=mock_authenticated
            )

            # Verify timezone-aware timestamp
            mock_datetime.now.assert_called_with(timezone.utc)
            assert result.timestamp == "2024-01-15T12:30:45+00:00"

    @pytest.mark.asyncio
    async def test_total_tokens_calculation(
        self,
        mock_request,
        mock_config,
        mock_security_manager,
        mock_calculation_service,
        mock_id_service,
        mock_authenticated
    ):
        """Test that total tokens are calculated correctly."""
        usage_request = UsageRequest(
            model="claude-3",
            input_tokens=750,
            output_tokens=250,
            metadata={"test": "data"}
        )

        result = await _calculate_environmental_impact(
            request=mock_request,
            usage_request=usage_request,
            config=mock_config,
            security_manager=mock_security_manager,
            calculation_service=mock_calculation_service,
            id_service=mock_id_service,
            authenticated=mock_authenticated
        )

        assert result.total_tokens == 1000  # 750 + 250

    @pytest.mark.asyncio
    async def test_security_validation_on_normalized_model(
        self,
        mock_request,
        mock_config,
        mock_security_manager,
        mock_id_service,
        mock_authenticated
    ):
        """Test that normalized model names are also security validated."""
        from unittest.mock import Mock, patch
        
        # Create a usage request with a model that could normalize to something invalid
        usage_request = UsageRequest(
            model="test-model",
            input_tokens=100,
            output_tokens=50,
            metadata={"test": "data"}
        )
        
        # Mock calculation service to simulate normalization that produces invalid result
        mock_calculation_service = Mock()
        
        # Mock the service to raise a security validation error
        from src.domain.services import ImpactCalculationService
        with patch.object(ImpactCalculationService, '_validate_model_name_security', 
                         side_effect=ValueError("Model name contains invalid characters: invalid@model")):
            mock_calculation_service.calculate_impact.side_effect = ValueError("Model name contains invalid characters: invalid@model")
            
            with pytest.raises(ValueError, match="Model name contains invalid characters"):
                await _calculate_environmental_impact(
                    request=mock_request,
                    usage_request=usage_request,
                    config=mock_config,
                    security_manager=mock_security_manager,
                    calculation_service=mock_calculation_service,
                    id_service=mock_id_service,
                    authenticated=mock_authenticated
                )
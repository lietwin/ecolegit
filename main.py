# main.py
import os
import json
import time
import hashlib
import hmac
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, field_validator
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Core calculator
from ecologits.impacts import Impacts
from ecologits.model_repository import models

# Security setup
security = HTTPBearer(auto_error=False)
limiter = Limiter(key_func=get_remote_address)

# Load configuration
def load_config():
    """Load configuration from file or environment"""
    config_path = Path("config.json")
    
    # Default configuration
    default_config = {
        "model_mappings": {
            "gpt-4o": "gpt-4o-2024-05-13",
            "gpt-4o-mini": "gpt-4o-mini-2024-07-18",
            "gpt-3.5-turbo": "gpt-3.5-turbo-0125",
            "gpt-4": "gpt-4-0613",
            "claude-3-opus": "claude-3-opus-20240229",
            "claude-3-sonnet": "claude-3-sonnet-20240229",
            "claude-3-haiku": "claude-3-haiku-20240307",
            "claude-3-5-sonnet": "claude-3-5-sonnet-20240620",
            "gemini-pro": "gemini-1.0-pro",
            "gemini-1.5-pro": "gemini-1.5-pro-001"
        },
        "security": {
            "enable_auth": False,
            "enable_webhook_signature": False,
            "max_tokens_per_request": 1000000,
            "trusted_hosts": ["*"]
        },
        "rate_limiting": {
            "requests_per_minute": 60,
            "enabled": True
        }
    }
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            return config
        except Exception as e:
            print(f"Warning: Error loading config file: {e}")
            return default_config
    else:
        # Create default config file
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"Created default config file: {config_path}")
        return default_config

# Load configuration
CONFIG = load_config()

# Request/Response models with validation
class UsageRequest(BaseModel):
    model: str = Field(..., min_length=1, max_length=100)
    input_tokens: int = Field(..., ge=0, le=CONFIG["security"]["max_tokens_per_request"])
    output_tokens: int = Field(..., ge=0, le=CONFIG["security"]["max_tokens_per_request"])
    metadata: Optional[Dict] = Field(default=None, max_length=10)
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        # Basic sanitization
        if not v.replace('-', '').replace('.', '').replace('_', '').isalnum():
            raise ValueError('Model name contains invalid characters')
        return v.strip().lower()
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v):
        if v is None:
            return v
        # Limit metadata size and depth
        serialized = json.dumps(v)
        if len(serialized) > 1000:  # 1KB limit
            raise ValueError('Metadata too large')
        return v

class ImpactResponse(BaseModel):
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

# FastAPI app with security middleware
app = FastAPI(
    title="EcoLogits Webhook",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=CONFIG["security"]["trusted_hosts"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://hook.eu1.make.com", "https://hook.us1.make.com"],  # Make.com domains
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Authentication functions
def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key if authentication is enabled"""
    if not CONFIG["security"]["enable_auth"]:
        return True
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    expected_key = os.getenv("API_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured"
        )
    
    if not hmac.compare_digest(credentials.credentials, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return True

def verify_webhook_signature(request: Request, body: bytes):
    """Verify webhook signature if enabled"""
    if not CONFIG["security"]["enable_webhook_signature"]:
        return True
    
    signature_header = request.headers.get("X-Webhook-Signature")
    if not signature_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook signature required"
        )
    
    webhook_secret = os.getenv("WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured"
        )
    
    expected_signature = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(f"sha256={expected_signature}", signature_header):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    return True

# Core calculation functions
def normalize_model(model_name: str) -> str:
    """Normalize model name using config mappings"""
    return CONFIG["model_mappings"].get(model_name.lower(), model_name)

def calculate_impact(model: str, input_tokens: int, output_tokens: int) -> Dict:
    """Calculate environmental impact with error handling"""
    try:
        # Input validation
        if input_tokens < 0 or output_tokens < 0:
            return {
                'energy_kwh': 0,
                'gwp_kgco2eq': 0,
                'success': False,
                'error': 'Token counts must be non-negative'
            }
        
        normalized_model = normalize_model(model)
        
        if normalized_model in models:
            ecologits_model = models[normalized_model]
            impacts = Impacts.from_model_and_tokens(
                model=ecologits_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            return {
                'energy_kwh': float(impacts.energy.value),
                'gwp_kgco2eq': float(impacts.gwp.value),
                'success': True,
                'normalized_model': normalized_model
            }
        else:
            return {
                'energy_kwh': 0,
                'gwp_kgco2eq': 0,
                'success': False,
                'error': f"Model '{normalized_model}' not supported"
            }
    except Exception as e:
        # Log error but don't expose internal details
        print(f"Calculation error: {e}")
        return {
            'energy_kwh': 0,
            'gwp_kgco2eq': 0,
            'success': False,
            'error': 'Internal calculation error'
        }

# API endpoints
@app.post("/calculate", response_model=ImpactResponse)
@limiter.limit(f"{CONFIG['rate_limiting']['requests_per_minute']}/minute")
async def calculate_environmental_impact(
    request: Request,
    usage_request: UsageRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Main webhook endpoint for Make.com
    Calculates environmental impact of AI model usage
    """
    
    # Get raw body for signature verification
    body = await request.body()
    verify_webhook_signature(request, body)
    
    # Calculate impact
    result = calculate_impact(
        model=usage_request.model,
        input_tokens=usage_request.input_tokens,
        output_tokens=usage_request.output_tokens
    )
    
    # Generate secure calculation ID
    calc_id = hashlib.sha256(
        f"{usage_request.model}-{usage_request.input_tokens}-{usage_request.output_tokens}-{time.time()}".encode()
    ).hexdigest()[:16]
    
    response = ImpactResponse(
        model=usage_request.model,
        input_tokens=usage_request.input_tokens,
        output_tokens=usage_request.output_tokens,
        total_tokens=usage_request.input_tokens + usage_request.output_tokens,
        energy_kwh=result['energy_kwh'],
        gwp_kgco2eq=result['gwp_kgco2eq'],
        calculation_id=f"calc-{calc_id}",
        timestamp=datetime.utcnow().isoformat(),
        success=result['success'],
        error=result.get('error')
    )
    
    return response

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ecologits-webhook",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/models")
async def get_supported_models():
    """Get list of supported models"""
    return {
        "supported_models": list(CONFIG["model_mappings"].keys()),
        "total_ecologits_models": len(models)
    }

# Remove test endpoint in production
if os.getenv("ENVIRONMENT") != "production":
    @app.get("/test")
    async def test_calculation():
        """Test calculation endpoint (dev only)"""
        result = calculate_impact("gpt-4o", 1000, 500)
        return {
            "test_model": "gpt-4o",
            "test_tokens": "1000 input + 500 output",
            "energy_kwh": result['energy_kwh'],
            "gwp_kgco2eq": result['gwp_kgco2eq'],
            "success": result['success'],
            "environment": "development"
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") != "production"
    )
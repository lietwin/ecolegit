"""Application constants."""

from enum import Enum


class Environment(str, Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class HTTPStatus(int, Enum):
    """HTTP status codes."""
    OK = 200
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500


class SecurityConstants:
    """Security-related constants."""
    MAX_TOKEN_COUNT = 1000000
    METADATA_SIZE_LIMIT_BYTES = 1000
    METADATA_MAX_ITEMS = 10
    CALCULATION_ID_LENGTH = 16
    

class DefaultValues:
    """Default configuration values."""
    DEFAULT_PORT = 8000
    DEFAULT_REQUESTS_PER_MINUTE = 60
    DEFAULT_CONFIG_FILE = "config.json"
    

class HeaderNames:
    """HTTP header names."""
    WEBHOOK_SIGNATURE = "X-Webhook-Signature"
    AUTHORIZATION = "Authorization"
    CONTENT_TYPE = "Content-Type"


class ConfigKeys:
    """Configuration keys."""
    MODEL_MAPPINGS = "model_mappings"
    SECURITY = "security"
    RATE_LIMITING = "rate_limiting"
    ENABLE_AUTH = "enable_auth"
    ENABLE_WEBHOOK_SIGNATURE = "enable_webhook_signature"
    MAX_TOKENS_PER_REQUEST = "max_tokens_per_request"
    TRUSTED_HOSTS = "trusted_hosts"
    REQUESTS_PER_MINUTE = "requests_per_minute"
    ENABLED = "enabled"


class EnvironmentVariables:
    """Environment variable names."""
    API_KEY = "API_KEY"
    WEBHOOK_SECRET = "WEBHOOK_SECRET"
    ENVIRONMENT = "ENVIRONMENT"
    PORT = "PORT"


class ErrorMessages:
    """Error message constants."""
    API_KEY_REQUIRED = "API key required"
    API_KEY_NOT_CONFIGURED = "API key not configured"
    INVALID_API_KEY = "Invalid API key"
    WEBHOOK_SIGNATURE_REQUIRED = "Webhook signature required"
    WEBHOOK_SECRET_NOT_CONFIGURED = "Webhook secret not configured"
    INVALID_WEBHOOK_SIGNATURE = "Invalid webhook signature"
    MODEL_NAME_INVALID_CHARS = "Model name contains invalid characters"
    METADATA_TOO_LARGE = "Metadata too large"
    TOKEN_COUNTS_NEGATIVE = "Token counts must be non-negative"
    MODEL_NOT_SUPPORTED = "Model '{model}' not supported"
    INTERNAL_CALCULATION_ERROR = "Internal calculation error"
    CONFIG_LOAD_ERROR = "Error loading config file"


class ModelMappings:
    """Model mappings from user-friendly names to EcoLogits model names.
    
    Uses 'latest' versions where available for automatic updates,
    falls back to specific versions for stability.
    """
    DEFAULT_MAPPINGS = {
        # OpenAI models - EcoLogits supports these directly
        "gpt-4o": "gpt-4o",
        "gpt4o": "gpt-4o",  # Typo correction
        "gpt-4o-mini": "gpt-4o-mini", 
        "gpt4o-mini": "gpt-4o-mini",  # Typo correction
        "gpt-4omini": "gpt-4o-mini",  # Typo correction  
        "gpt4omini": "gpt-4o-mini",   # Typo correction
        "gpt-3.5-turbo": "gpt-3.5-turbo",
        "gpt35turbo": "gpt-3.5-turbo",   # Typo correction
        "gpt3.5turbo": "gpt-3.5-turbo", # Typo correction
        "gpt-4": "gpt-4",
        "gpt4": "gpt-4",  # Typo correction
        
        # Anthropic models - prefer latest versions for auto-updates
        "claude-3-opus": "claude-3-opus-latest",
        "claude3opus": "claude-3-opus-latest",    # Typo correction
        "claudeopus": "claude-3-opus-latest",     # Typo correction
        "claude-3-sonnet": "claude-3-5-sonnet-latest",  # Use 3.5 as it's newer
        "claude3sonnet": "claude-3-5-sonnet-latest",     # Typo correction
        "claudesonnet": "claude-3-5-sonnet-latest",      # Typo correction  
        "claude-3-5-sonnet": "claude-3-5-sonnet-latest",
        "claude35sonnet": "claude-3-5-sonnet-latest",    # Typo correction
        "claude-35-sonnet": "claude-3-5-sonnet-latest",  # Typo correction
        "claude-3-haiku": "claude-3-5-haiku-latest",     # Use 3.5 as it's newer
        "claude3haiku": "claude-3-5-haiku-latest",       # Typo correction
        "claudehaiku": "claude-3-5-haiku-latest",        # Typo correction
        "claude-3-5-haiku": "claude-3-5-haiku-latest",
        
        # Google models - use latest Gemini 2.0/2.5 models that EcoLogits supports
        "gemini-pro": "gemini-2.5-pro",         # Use latest 2.5 pro
        "geminipro": "gemini-2.5-pro",          # Typo correction
        "gemini-1.5-pro": "gemini-2.5-pro",     # Upgrade to 2.5
        "gemini15pro": "gemini-2.5-pro",        # Typo correction
        "gemini-15-pro": "gemini-2.5-pro",      # Typo correction
        "gemini-flash": "gemini-2.5-flash",     # Use latest 2.5 flash
        "geminiflash": "gemini-2.5-flash",      # Typo correction
        "gemini-2.0-flash": "gemini-2.5-flash", # Upgrade to 2.5
        "gemini-2.5-flash": "gemini-2.5-flash", # Latest flash model
        "gemini-2.5-pro": "gemini-2.5-pro",     # Latest pro model
        
        # Support exact EcoLogits names as pass-through
        "claude-3-opus-latest": "claude-3-opus-latest",
        "claude-3-5-sonnet-latest": "claude-3-5-sonnet-latest", 
        "claude-3-5-haiku-latest": "claude-3-5-haiku-latest",
        "chatgpt-4o-latest": "chatgpt-4o-latest",
        
        # Support legacy versioned names for backward compatibility
        "claude-3-opus-20240229": "claude-3-opus-20240229",
        "claude-3-sonnet-20240229": "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307": "claude-3-haiku-20240307", 
        "claude-3-5-sonnet-20240620": "claude-3-5-sonnet-20240620",
        "gpt-4o-2024-05-13": "gpt-4o",
        "gpt-4o-mini-2024-07-18": "gpt-4o-mini",
        "gpt-3.5-turbo-0125": "gpt-3.5-turbo",
        # Legacy Google model names - upgrade to latest
        "gemini-1.0-pro": "gemini-2.5-pro",
        "gemini-1.5-pro-001": "gemini-2.5-pro"
    }


class CORSSettings:
    """CORS configuration."""
    ALLOWED_ORIGINS = [
        "https://hook.eu1.make.com",
        "https://hook.us1.make.com"
    ]
    ALLOWED_METHODS = ["POST"]
    ALLOWED_HEADERS = ["Content-Type", "Authorization"]
    ALLOW_CREDENTIALS = False
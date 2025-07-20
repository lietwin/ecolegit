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
    """Default model mappings from versioned model names to EcoLogits model names."""
    DEFAULT_MAPPINGS = {
        # OpenAI models - map versioned names to simple names EcoLogits expects
        "gpt-4o-2024-05-13": "gpt-4o",
        "gpt4o-2024-05-13": "gpt-4o",  # Handle both formats
        "gpt-4o-mini-2024-07-18": "gpt-4o-mini",
        "gpt4o-mini-2024-07-18": "gpt-4o-mini",
        "gpt-3.5-turbo-0125": "gpt-3.5-turbo",
        "gpt-4-0613": "gpt-4",
        # Anthropic models
        "claude-3-opus-20240229": "claude-3-opus",
        "claude-3-sonnet-20240229": "claude-3-sonnet", 
        "claude-3-haiku-20240307": "claude-3-haiku",
        "claude-3-5-sonnet-20240620": "claude-3-5-sonnet",
        # Google models
        "gemini-1.0-pro": "gemini-pro",
        "gemini-1.5-pro-001": "gemini-1.5-pro",
        # Also support direct simple names (pass-through)
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-3.5-turbo": "gpt-3.5-turbo",
        "gpt-4": "gpt-4"
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
"""Configuration management."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from .constants import (
    DefaultValues,
    ConfigKeys,
    EnvironmentVariables,
    ErrorMessages,
    ModelMappings,
    CORSSettings,
    SecurityConstants,
    Environment
)

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Security configuration."""
    enable_auth: bool = False
    enable_webhook_signature: bool = False
    max_tokens_per_request: int = SecurityConstants.MAX_TOKEN_COUNT
    trusted_hosts: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = DefaultValues.DEFAULT_REQUESTS_PER_MINUTE
    enabled: bool = True


@dataclass
class CORSConfig:
    """CORS configuration."""
    allowed_origins: List[str] = field(default_factory=lambda: CORSSettings.ALLOWED_ORIGINS)
    allowed_methods: List[str] = field(default_factory=lambda: CORSSettings.ALLOWED_METHODS)
    allowed_headers: List[str] = field(default_factory=lambda: CORSSettings.ALLOWED_HEADERS)
    allow_credentials: bool = CORSSettings.ALLOW_CREDENTIALS


@dataclass
class AppConfig:
    """Application configuration."""
    model_mappings: Dict[str, str] = field(default_factory=lambda: ModelMappings.DEFAULT_MAPPINGS.copy())
    security: SecurityConfig = field(default_factory=SecurityConfig)
    rate_limiting: RateLimitConfig = field(default_factory=RateLimitConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)
    environment: Environment = Environment.DEVELOPMENT
    port: int = DefaultValues.DEFAULT_PORT
    api_key: Optional[str] = None
    webhook_secret: Optional[str] = None

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "AppConfig":
        """Create configuration from dictionary."""
        security_dict = config_dict.get(ConfigKeys.SECURITY, {})
        rate_limit_dict = config_dict.get(ConfigKeys.RATE_LIMITING, {})
        
        return cls(
            model_mappings=config_dict.get(ConfigKeys.MODEL_MAPPINGS, ModelMappings.DEFAULT_MAPPINGS.copy()),
            security=SecurityConfig(
                enable_auth=security_dict.get(ConfigKeys.ENABLE_AUTH, False),
                enable_webhook_signature=security_dict.get(ConfigKeys.ENABLE_WEBHOOK_SIGNATURE, False),
                max_tokens_per_request=security_dict.get(ConfigKeys.MAX_TOKENS_PER_REQUEST, SecurityConstants.MAX_TOKEN_COUNT),
                trusted_hosts=security_dict.get(ConfigKeys.TRUSTED_HOSTS, ["*"])
            ),
            rate_limiting=RateLimitConfig(
                requests_per_minute=rate_limit_dict.get(ConfigKeys.REQUESTS_PER_MINUTE, DefaultValues.DEFAULT_REQUESTS_PER_MINUTE),
                enabled=rate_limit_dict.get(ConfigKeys.ENABLED, True)
            ),
            environment=Environment(os.getenv(EnvironmentVariables.ENVIRONMENT, Environment.DEVELOPMENT)),
            port=int(os.getenv(EnvironmentVariables.PORT, DefaultValues.DEFAULT_PORT)),
            api_key=os.getenv(EnvironmentVariables.API_KEY),
            webhook_secret=os.getenv(EnvironmentVariables.WEBHOOK_SECRET)
        )

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary for serialization."""
        return {
            ConfigKeys.MODEL_MAPPINGS: self.model_mappings,
            ConfigKeys.SECURITY: {
                ConfigKeys.ENABLE_AUTH: self.security.enable_auth,
                ConfigKeys.ENABLE_WEBHOOK_SIGNATURE: self.security.enable_webhook_signature,
                ConfigKeys.MAX_TOKENS_PER_REQUEST: self.security.max_tokens_per_request,
                ConfigKeys.TRUSTED_HOSTS: self.security.trusted_hosts
            },
            ConfigKeys.RATE_LIMITING: {
                ConfigKeys.REQUESTS_PER_MINUTE: self.rate_limiting.requests_per_minute,
                ConfigKeys.ENABLED: self.rate_limiting.enabled
            }
        }


class ConfigurationError(Exception):
    """Configuration related errors."""
    pass


class ConfigLoader:
    """Configuration loader with proper error handling."""

    def __init__(self, config_file: str = DefaultValues.DEFAULT_CONFIG_FILE):
        self.config_file = Path(config_file)

    def load(self) -> AppConfig:
        """Load configuration from file or create default."""
        try:
            if self.config_file.exists():
                return self._load_from_file()
            else:
                return self._create_default_config()
        except Exception as e:
            logger.error(f"{ErrorMessages.CONFIG_LOAD_ERROR}: {e}")
            raise ConfigurationError(f"{ErrorMessages.CONFIG_LOAD_ERROR}: {e}") from e

    def _load_from_file(self) -> AppConfig:
        """Load configuration from existing file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # Merge with defaults to ensure all keys are present
            config = AppConfig.from_dict(config_dict)
            logger.info(f"Configuration loaded from {self.config_file}")
            return config
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in config file {self.config_file}: {e}")
            return self._create_default_config()
        except (IOError, OSError) as e:
            logger.warning(f"Error reading config file {self.config_file}: {e}")
            return self._create_default_config()

    def _create_default_config(self) -> AppConfig:
        """Create and save default configuration."""
        config = AppConfig()
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2)
            logger.info(f"Created default config file: {self.config_file}")
        except (IOError, OSError) as e:
            logger.warning(f"Could not create config file {self.config_file}: {e}")
        
        return config

    def save(self, config: AppConfig) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except (IOError, OSError) as e:
            logger.error(f"Error saving config file {self.config_file}: {e}")
            raise ConfigurationError(f"Error saving config file: {e}") from e
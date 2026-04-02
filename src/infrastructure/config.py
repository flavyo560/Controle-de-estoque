"""Configuration management with environment variable validation."""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
import os


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="DEKIDS")
    app_version: str = Field(default="2.0.0")
    environment: Literal["development", "testing", "staging", "production"] = Field(
        default="development"
    )
    debug: bool = Field(default=False)
    
    # Database
    database_url: str = Field(...)  # Required
    database_pool_min: int = Field(default=10)
    database_pool_max: int = Field(default=20)
    database_timeout: float = Field(default=60.0)
    
    # Security
    secret_key: str = Field(...)  # Required
    encryption_key: str = Field(...)  # Required
    session_duration_hours: int = Field(default=8)
    password_min_length: int = Field(default=12)
    max_login_attempts: int = Field(default=5)
    lockout_duration_minutes: int = Field(default=30)
    
    # Cache
    cache_backend: Literal["memory", "redis"] = Field(default="memory")
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    cache_default_ttl: int = Field(default=300)
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    log_file: str = Field(default="logs/dekids.log")
    log_rotation: str = Field(default="daily")
    log_retention_days: int = Field(default=90)
    
    # Performance
    query_slow_threshold_ms: int = Field(default=1000)
    async_operation_threshold_ms: int = Field(default=100)
    max_concurrent_operations: int = Field(default=5)
    
    # File Upload
    max_upload_size_mb: int = Field(default=10)
    allowed_file_extensions: list[str] = Field(default=["csv", "pdf", "jpg", "png"])
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL is properly formatted."""
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v
    
    @field_validator("secret_key", "encryption_key")
    @classmethod
    def validate_keys(cls, v: str) -> str:
        """Ensure security keys are sufficiently long."""
        if len(v) < 32:
            raise ValueError("Security keys must be at least 32 characters")
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton.
    
    Returns:
        Settings instance loaded from environment
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def validate_required_settings() -> None:
    """
    Validate that all required settings are present.
    Called at application startup.
    
    Raises:
        ValueError: If required settings are missing or invalid
    """
    try:
        settings = get_settings()
        
        # Log configuration summary (without sensitive data)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Application: {settings.app_name} v{settings.app_version}")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"Cache backend: {settings.cache_backend}")
        logger.info(f"Log level: {settings.log_level}")
        
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}")

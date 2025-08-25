"""Configuration management for VILS backend."""

import os
from typing import List, Optional

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "Version Issue Locator System"
    environment: str = "development"
    debug: bool = False
    api_prefix: str = "/api"

    # Database
    database_url: PostgresDsn
    db_pool_size: int = 20
    db_max_overflow: int = 40

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl: int = 3600

    # Security
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    encryption_master_key: str

    # External Services
    jenkins_url: Optional[str] = None
    jenkins_token: Optional[str] = None
    github_token: Optional[str] = None
    gitlab_token: Optional[str] = None

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Monitoring
    sentry_dsn: Optional[str] = None
    log_level: str = "INFO"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError("CORS origins must be a string or list")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
from __future__ import annotations

import json
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Procura AI", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    # Database
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    # Redis
    redis_url: str | None = Field(default=None, alias="REDIS_URL")

    # Security
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    jwt_secret: str | None = Field(default=None, alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # CORS
    allowed_origins: list[str] = Field(default=["http://localhost:3000"], alias="ALLOWED_ORIGINS")

    # Logging
    log_level: str = Field(default="DEBUG", alias="LOG_LEVEL")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("app_env", mode="before")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        valid = {"development", "staging", "production", "test"}
        lowered = v.lower()
        if lowered not in valid:
            msg = f"Invalid environment: {v}. Must be one of {valid}"
            raise ValueError(msg)
        return lowered

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_staging(self) -> bool:
        return self.app_env == "staging"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"

    @property
    def resolved_jwt_secret(self) -> str:
        return self.jwt_secret or self.secret_key

    @property
    def log_level_int(self) -> int:
        import logging

        return getattr(logging, self.log_level.upper(), logging.DEBUG)

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    @property
    def log_dir(self) -> Path:
        path = self.base_dir / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

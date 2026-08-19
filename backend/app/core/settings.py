from __future__ import annotations

import json
import secrets
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Procura AI", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE", ge=1)
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW", ge=0)
    db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT", gt=0)
    db_pool_recycle: int = Field(default=1800, alias="DB_POOL_RECYCLE", gt=0)
    db_pool_pre_ping: bool = Field(default=True, alias="DB_POOL_PRE_PING")
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    redis_url: str | None = Field(default=None, alias="REDIS_URL")

    secret_key: str = Field(default="", alias="SECRET_KEY")
    jwt_secret: str | None = Field(default=None, alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES", gt=0)
    refresh_token_expire_days: int = Field(default=30, alias="REFRESH_TOKEN_EXPIRE_DAYS", gt=0)
    password_argon2_memory: int = Field(default=19456, alias="PASSWORD_ARGON2_MEMORY", gt=0)
    password_argon2_time: int = Field(default=2, alias="PASSWORD_ARGON2_TIME", gt=0)
    password_argon2_parallelism: int = Field(default=1, alias="PASSWORD_ARGON2_PARALLELISM", gt=0)

    allowed_origins: list[str] = Field(default_factory=list, alias="ALLOWED_ORIGINS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if not isinstance(parsed, list):
                    raise ValueError("ALLOWED_ORIGINS must be a JSON list")
                return [str(origin) for origin in parsed]
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("app_env", mode="before")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        valid = {"development", "staging", "production", "test"}
        lowered = str(v).lower()
        if lowered not in valid:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid}")
        return lowered

    @field_validator("jwt_algorithm")
    @classmethod
    def validate_jwt_algorithm(cls, v: str) -> str:
        allowed = {"HS256", "HS384", "HS512"}
        if v not in allowed:
            raise ValueError(f"Unsupported JWT algorithm: {v}")
        return v

    @model_validator(mode="after")
    def validate_configuration(self) -> Settings:
        if not self.is_production:
            if not self.secret_key:
                self.secret_key = secrets.token_urlsafe(32)
            return self

        if len(self.secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        if not self.jwt_secret or len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters in production")
        if not self.database_url:
            raise ValueError("DATABASE_URL is required in production")
        if not self.redis_url:
            raise ValueError("REDIS_URL is required in production")
        if self.debug:
            raise ValueError("DEBUG must be false in production")
        if not self.allowed_origins:
            raise ValueError("ALLOWED_ORIGINS must be configured in production")
        if self.log_level.upper() == "DEBUG":
            raise ValueError("LOG_LEVEL must not be DEBUG in production")
        return self

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

        return getattr(logging, self.log_level.upper(), logging.INFO)

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    @property
    def log_dir(self) -> Path:
        path = self.base_dir / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

from __future__ import annotations

from pydantic import ValidationError
import pytest

from app.core.settings import Settings


def test_development_settings_generate_secret() -> None:
    settings = Settings(app_env="development")

    assert settings.secret_key
    assert len(settings.secret_key) >= 32


def test_production_requires_database_url() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL is required in production"):
        Settings(
            app_env="production",
            secret_key="s" * 32,
            jwt_secret="j" * 32,
            redis_url="redis://localhost:6379/0",
            allowed_origins=["https://example.com"],
        )


def test_production_requires_redis_url() -> None:
    with pytest.raises(ValidationError, match="REDIS_URL is required in production"):
        Settings(
            app_env="production",
            secret_key="s" * 32,
            jwt_secret="j" * 32,
            database_url="postgresql+asyncpg://user:password@localhost/procura",
            allowed_origins=["https://example.com"],
        )


def test_production_rejects_debug() -> None:
    with pytest.raises(ValidationError, match="DEBUG must be false in production"):
        Settings(
            app_env="production",
            debug=True,
            secret_key="s" * 32,
            jwt_secret="j" * 32,
            database_url="postgresql+asyncpg://user:password@localhost/procura",
            redis_url="redis://localhost:6379/0",
            allowed_origins=["https://example.com"],
        )


def test_production_requires_cors_origins() -> None:
    with pytest.raises(ValidationError, match="ALLOWED_ORIGINS must be configured in production"):
        Settings(
            app_env="production",
            secret_key="s" * 32,
            jwt_secret="j" * 32,
            database_url="postgresql+asyncpg://user:password@localhost/procura",
            redis_url="redis://localhost:6379/0",
        )

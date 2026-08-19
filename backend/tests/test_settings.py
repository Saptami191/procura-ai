from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.settings import Settings


# Production-only configuration used by the validation tests.
PRODUCTION_VALUES = {
    "app_env": "production",
    "secret_key": "s" * 32,
    "jwt_secret": "j" * 32,
    "database_url": "postgresql+asyncpg://user:password@localhost:5432/procura",
    "redis_url": "redis://localhost:6379/0",
    "allowed_origins": ["https://app.example.com"],
    "debug": False,
    "log_level": "INFO",
}


def test_production_configuration_is_accepted() -> None:
    settings = Settings(**PRODUCTION_VALUES)

    assert settings.is_production is True
    assert settings.resolved_jwt_secret == "j" * 32


@pytest.mark.parametrize(
    "field, value",
    [
        ("secret_key", "short"),
        ("jwt_secret", "short"),
        ("database_url", None),
        ("redis_url", None),
        ("allowed_origins", []),
        ("debug", True),
        ("log_level", "DEBUG"),
    ],
)
def test_production_configuration_rejects_unsafe_values(field: str, value: object) -> None:
    values = {**PRODUCTION_VALUES, field: value}

    with pytest.raises(ValidationError):
        Settings(**values)


def test_development_configuration_generates_a_secret_when_missing() -> None:
    settings = Settings(app_env="development", secret_key="")

    assert len(settings.secret_key) >= 32

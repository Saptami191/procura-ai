from __future__ import annotations

from enum import StrEnum


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class Role(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class Permission(StrEnum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class PaginationDefaults:
    DEFAULT_PAGE: int = 1
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


class HTTPLimits:
    MAX_BODY_SIZE: int = 10 * 1024 * 1024
    MAX_FILE_SIZE: int = 50 * 1024 * 1024
    RATE_LIMIT_PER_MINUTE: int = 60


class TimeConstants:
    DEFAULT_TIMEZONE: str = "UTC"
    SECONDS_IN_MINUTE: int = 60
    MINUTES_IN_HOUR: int = 60
    HOURS_IN_DAY: int = 24


class API:
    VERSION: str = "v1"
    PREFIX: str = "/api/v1"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"


class Logging:
    DEFAULT_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    JSON_FORMAT: str = (
        '{{"time":"{time:YYYY-MM-DD HH:mm:ss.SSS}",'
        '"level":"{level}",'
        '"name":"{name}",'
        '"function":"{function}",'
        '"line":{line},'
        '"message":"{message}"'
        "}}"
    )
    FILE_ROTATION: str = "1 day"
    FILE_RETENTION: str = "30 days"
    FILE_COMPRESSION: str = "zip"


class SecurityHeaders:
    X_CONTENT_TYPE_OPTIONS: str = "nosniff"
    X_FRAME_OPTIONS: str = "DENY"
    X_XSS_PROTECTION: str = "1; mode=block"
    STRICT_TRANSPORT_SECURITY: str = "max-age=31536000; includeSubDomains"
    CACHE_CONTROL: str = "no-store"
    PRAGMA: str = "no-cache"

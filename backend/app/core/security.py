from __future__ import annotations

from datetime import timedelta


class PasswordPolicy:
    MIN_LENGTH: int = 8
    MAX_LENGTH: int = 128
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_LOWERCASE: bool = True
    REQUIRE_DIGIT: bool = True
    REQUIRE_SPECIAL: bool = True
    BCRYPT_ROUNDS: int = 12
    RESET_TOKEN_EXPIRE_HOURS: int = 24


class TokenDefaults:
    ACCESS_TOKEN_EXPIRE: timedelta = timedelta(minutes=30)
    REFRESH_TOKEN_EXPIRE: timedelta = timedelta(days=7)
    TOKEN_TYPE: str = "bearer"
    TOKEN_ISSUER: str = "procura-ai"
    TOKEN_AUDIENCE: str = "procura-ai-api"


class CORSDefaults:
    ALLOWED_METHODS: list[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: list[str] = [
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Correlation-ID",
    ]
    ALLOW_CREDENTIALS: bool = True
    MAX_AGE: int = 600


class SecurityHeaderDefaults:
    X_CONTENT_TYPE_OPTIONS: str = "nosniff"
    X_FRAME_OPTIONS: str = "DENY"
    X_XSS_PROTECTION: str = "1; mode=block"
    STRICT_TRANSPORT_SECURITY: str = "max-age=31536000; includeSubDomains"
    CACHE_CONTROL: str = "no-store"
    PRAGMA: str = "no-cache"
    CONTENT_SECURITY_POLICY: str = "default-src 'self'"
    PERMISSIONS_POLICY: str = "geolocation=(), microphone=(), camera=()"


def validate_password_strength(password: str) -> list[str]:
    errors: list[str] = []

    if len(password) < PasswordPolicy.MIN_LENGTH:
        errors.append(f"Password must be at least {PasswordPolicy.MIN_LENGTH} characters")

    if len(password) > PasswordPolicy.MAX_LENGTH:
        errors.append(f"Password must be at most {PasswordPolicy.MAX_LENGTH} characters")

    if PasswordPolicy.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if PasswordPolicy.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if PasswordPolicy.REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
    if PasswordPolicy.REQUIRE_SPECIAL and not any(c in special_chars for c in password):
        errors.append("Password must contain at least one special character")

    return errors

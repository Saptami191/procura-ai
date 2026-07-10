from __future__ import annotations

from typing import Any

from app.core.exceptions import AppException


class AuthException(AppException):
    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "AUTH_ERROR",
        status_code: int = 401,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            details=details,
        )


class InvalidCredentialsException(AuthException):
    def __init__(
        self,
        message: str = "Invalid email or password",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="INVALID_CREDENTIALS",
            details=details,
        )


class InvalidTokenException(AuthException):
    def __init__(
        self,
        message: str = "Invalid or malformed token",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="INVALID_TOKEN",
            details=details,
        )


class ExpiredTokenException(AuthException):
    def __init__(
        self,
        message: str = "Token has expired",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="EXPIRED_TOKEN",
            details=details,
        )


class RevokedTokenException(AuthException):
    def __init__(
        self,
        message: str = "Token has been revoked",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="REVOKED_TOKEN",
            details=details,
        )


class InactiveSessionException(AuthException):
    def __init__(
        self,
        message: str = "Session is no longer active",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="INACTIVE_SESSION",
            details=details,
        )

from __future__ import annotations

from typing import Any

from app.core.exceptions import (
    AppException,
    ConflictException,
    NotFoundException,
    ValidationException,
)


class UserError(AppException):
    def __init__(
        self,
        message: str = "User operation failed",
        code: str = "USER_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=status_code, details=details)


class UserNotFoundError(NotFoundException):
    def __init__(
        self,
        user_id: str | None = None,
        email: str | None = None,
        username: str | None = None,
    ) -> None:
        identifier = user_id or email or username or "unknown"
        super().__init__(
            message=f"User '{identifier}' not found",
            details={"user_id": user_id, "email": email, "username": username},
        )


class DuplicateEmailError(ConflictException):
    def __init__(self, email: str) -> None:
        super().__init__(
            message=f"User with email '{email}' already exists",
            details={"field": "email", "value": email},
        )


class DuplicateUsernameError(ConflictException):
    def __init__(self, username: str) -> None:
        super().__init__(
            message=f"User with username '{username}' already exists",
            details={"field": "username", "value": username},
        )


class DuplicatePhoneError(ConflictException):
    def __init__(self, phone: str) -> None:
        super().__init__(
            message=f"User with phone '{phone}' already exists",
            details={"field": "phone", "value": phone},
        )


class InactiveUserError(UserError):
    def __init__(self, user_id: str) -> None:
        super().__init__(
            message=f"User '{user_id}' is inactive",
            code="INACTIVE_USER",
            status_code=403,
            details={"user_id": user_id},
        )


class UserValidationError(ValidationException):
    def __init__(
        self,
        message: str = "User validation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)

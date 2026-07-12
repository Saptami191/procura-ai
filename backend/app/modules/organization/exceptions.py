from __future__ import annotations

from typing import Any

from app.core.exceptions import AppException, ValidationException


class OrganizationError(AppException):
    def __init__(
        self,
        message: str = "Organization operation failed",
        code: str = "ORGANIZATION_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            details=details,
        )


class OrganizationNotFoundError(OrganizationError):
    def __init__(
        self,
        organization_id: str | None = None,
        slug: str | None = None,
    ) -> None:
        identifier = organization_id or slug or "unknown"
        super().__init__(
            message=f"Organization '{identifier}' not found",
            code="NOT_FOUND",
            status_code=404,
            details={"organization_id": organization_id, "slug": slug},
        )


class OrganizationAlreadyExistsError(OrganizationError):
    def __init__(
        self,
        field: str,
        value: str,
    ) -> None:
        super().__init__(
            message=f"Organization with {field} '{value}' already exists",
            code="CONFLICT",
            status_code=409,
            details={"field": field, "value": value},
        )


class OrganizationInactiveError(OrganizationError):
    def __init__(
        self,
        organization_id: str,
        status: str = "inactive",
    ) -> None:
        super().__init__(
            message=f"Organization '{organization_id}' is {status}",
            code="ORGANIZATION_INACTIVE",
            status_code=403,
            details={"organization_id": organization_id, "status": status},
        )


class OrganizationValidationError(ValidationException):
    def __init__(
        self,
        message: str = "Organization validation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            details=details,
        )

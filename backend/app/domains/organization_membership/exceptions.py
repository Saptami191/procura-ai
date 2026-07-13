from __future__ import annotations

from typing import Any

from app.core.exceptions import (
    AppException,
    ConflictException,
    NotFoundException,
    ValidationException,
)


class MembershipError(AppException):
    def __init__(
        self,
        message: str = "Membership operation failed",
        code: str = "MEMBERSHIP_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=status_code, details=details)


class MembershipNotFoundError(NotFoundException):
    def __init__(
        self,
        membership_id: str | None = None,
        organization_id: str | None = None,
        user_id: str | None = None,
    ) -> None:
        identifier = membership_id or f"org={organization_id},user={user_id}" or "unknown"
        super().__init__(
            message=f"Membership '{identifier}' not found",
            details={
                "membership_id": membership_id,
                "organization_id": organization_id,
                "user_id": user_id,
            },
        )


class MembershipAlreadyExistsError(ConflictException):
    def __init__(self, organization_id: str, user_id: str) -> None:
        super().__init__(
            message="User is already a member of this organization",
            details={"organization_id": organization_id, "user_id": user_id},
        )


class InvalidMembershipStateError(ValidationException):
    def __init__(
        self,
        current_status: str,
        required_status: str | list[str],
        action: str,
    ) -> None:
        if isinstance(required_status, str):
            required = required_status
        else:
            required = ", ".join(required_status)
        super().__init__(
            message=(
                f"Cannot {action} membership in '{current_status}' status. "
                f"Required: {required}"
            ),
            details={
                "current_status": current_status,
                "required_status": required,
                "action": action,
            },
        )


class CannotRemoveOwnerError(MembershipError):
    def __init__(self, membership_id: str) -> None:
        super().__init__(
            message="Cannot remove the organization owner. Transfer ownership first.",
            code="CANNOT_REMOVE_OWNER",
            status_code=403,
            details={"membership_id": membership_id},
        )


class CannotRemoveLastOwnerError(MembershipError):
    def __init__(self, organization_id: str) -> None:
        super().__init__(
            message=(
                "Cannot remove the last owner of the organization. "
                "Every organization must have at least one owner."
            ),
            code="CANNOT_REMOVE_LAST_OWNER",
            status_code=403,
            details={"organization_id": organization_id},
        )


class DefaultOrganizationError(MembershipError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="DEFAULT_ORGANIZATION_ERROR",
            status_code=400,
            details=details,
        )


class OrganizationNotActiveError(MembershipError):
    def __init__(self, organization_id: str) -> None:
        super().__init__(
            message="Organization is not active. Cannot manage memberships.",
            code="ORGANIZATION_NOT_ACTIVE",
            status_code=400,
            details={"organization_id": organization_id},
        )


class UserNotActiveError(MembershipError):
    def __init__(self, user_id: str) -> None:
        super().__init__(
            message="User is not active. Cannot create membership.",
            code="USER_NOT_ACTIVE",
            status_code=400,
            details={"user_id": user_id},
        )


class MembershipValidationError(ValidationException):
    def __init__(
        self,
        message: str = "Membership validation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)

from __future__ import annotations

from app.core.exceptions import (
    AppException,
    AuthorizationException,
    ConflictException,
    NotFoundException,
    ValidationException,
)


class RoleNotFoundError(NotFoundException):
    def __init__(self, role_id: str | None = None, slug: str | None = None) -> None:
        identifier = role_id or slug or "unknown"
        super().__init__(
            message=f"Role '{identifier}' not found",
            details={"role_id": role_id, "slug": slug},
        )


class PermissionNotFoundError(NotFoundException):
    def __init__(
        self, permission_id: str | None = None, code: str | None = None,
    ) -> None:
        identifier = permission_id or code or "unknown"
        super().__init__(
            message=f"Permission '{identifier}' not found",
            details={"permission_id": permission_id, "code": code},
        )


class DuplicateRoleError(ConflictException):
    def __init__(self, name: str, organization_id: str | None = None) -> None:
        super().__init__(
            message=f"Role '{name}' already exists",
            details={"name": name, "organization_id": organization_id},
        )


class DuplicatePermissionError(ConflictException):
    def __init__(self, code: str) -> None:
        super().__init__(
            message=f"Permission code '{code}' already exists",
            details={"code": code},
        )


class RoleAssignmentError(AppException):
    def __init__(
        self, message: str = "Role assignment failed", details: dict | None = None,
    ) -> None:
        super().__init__(
            message=message, code="ROLE_ASSIGNMENT_ERROR",
            status_code=400, details=details,
        )


class PermissionAssignmentError(AppException):
    def __init__(
        self, message: str = "Permission assignment failed",
        details: dict | None = None,
    ) -> None:
        super().__init__(
            message=message, code="PERMISSION_ASSIGNMENT_ERROR",
            status_code=400, details=details,
        )


class PermissionDeniedError(AuthorizationException):
    def __init__(self, permission_code: str) -> None:
        super().__init__(
            message=f"Missing required permission: {permission_code}",
            details={"required_permission": permission_code},
        )


class SystemRoleModificationError(ValidationException):
    def __init__(self, action: str, role_name: str) -> None:
        super().__init__(
            message=f"Cannot {action} system role '{role_name}'",
            details={"action": action, "role_name": role_name},
        )

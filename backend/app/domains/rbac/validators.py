from __future__ import annotations

import re
from typing import Any

from app.domains.rbac.exceptions import (
    DuplicatePermissionError,
    DuplicateRoleError,
    PermissionNotFoundError,
    RoleNotFoundError,
    SystemRoleModificationError,
)
from app.domains.rbac.models import Permission, Role


def validate_role_name(name: str) -> str:
    stripped = name.strip()
    if len(stripped) < 1:
        raise ValueError("Role name cannot be empty")
    if len(stripped) > 100:
        raise ValueError("Role name cannot exceed 100 characters")
    return stripped


def validate_slug(name: str) -> str:
    slug = name.strip().lower().replace(" ", "_")
    if not re.match(r"^[a-z][a-z0-9_]*$", slug):
        raise ValueError(
            "Slug must start with a letter and contain only "
            "lowercase letters, digits, and underscores",
        )
    return slug


def validate_permission_code(resource: str, action: str) -> str:
    return f"{resource}.{action}"


def check_duplicate_role(
    role: Role | None,
    name: str | None = None,
    slug: str | None = None,
) -> None:
    if role is not None:
        raise DuplicateRoleError(name=name or role.name)


def check_duplicate_permission(permission: Permission | None, code: str) -> None:
    if permission is not None:
        raise DuplicatePermissionError(code=code)


def check_role_exists(role: Role | None, role_id: str) -> Role:
    if role is None:
        raise RoleNotFoundError(role_id=role_id)
    return role


def check_permission_exists(
    permission: Permission | None, permission_id: str,
) -> Permission:
    if permission is None:
        raise PermissionNotFoundError(permission_id=permission_id)
    return permission


def ensure_not_system_role(role: Role, action: str) -> None:
    if role.is_system_role:
        raise SystemRoleModificationError(action=action, role_name=role.name)


def validate_role_assignment_data(data: dict[str, Any]) -> dict[str, Any]:
    validated: dict[str, Any] = {}
    if "name" in data and data["name"] is not None:
        validated["name"] = validate_role_name(str(data["name"]))
    if "slug" in data and data["slug"] is not None:
        validated["slug"] = validate_slug(str(data["slug"]))
    if "description" in data and data["description"] is not None:
        validated["description"] = str(data["description"]).strip()
    if "priority" in data and data["priority"] is not None:
        validated["priority"] = int(data["priority"])
    if "metadata" in data and data["metadata"] is not None:
        validated["metadata"] = data["metadata"]
    return validated


def validate_permission_update_data(data: dict[str, Any]) -> dict[str, Any]:
    validated: dict[str, Any] = {}
    if "description" in data and data["description"] is not None:
        validated["description"] = str(data["description"]).strip()
    if "category" in data and data["category"] is not None:
        validated["category"] = data["category"]
    if "metadata" in data and data["metadata"] is not None:
        validated["metadata"] = data["metadata"]
    return validated

from __future__ import annotations

import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.db.dependencies import get_db
from app.domains.rbac.exceptions import PermissionDeniedError
from app.domains.rbac.middleware import MEMBERSHIP_ID_CONTEXT
from app.domains.rbac.repository import (
    MembershipRoleRepository,
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
)
from app.domains.rbac.schemas import CurrentPermissionsResponse
from app.domains.rbac.service import AuthorizationService

# ── Repository Dependencies ─────────────────────────────────────

async def get_role_repository(
    session: AsyncSession = Depends(get_db),
) -> RoleRepository:
    return RoleRepository(session)


async def get_permission_repository(
    session: AsyncSession = Depends(get_db),
) -> PermissionRepository:
    return PermissionRepository(session)


async def get_role_permission_repository(
    session: AsyncSession = Depends(get_db),
) -> RolePermissionRepository:
    return RolePermissionRepository(session)


async def get_membership_role_repository(
    session: AsyncSession = Depends(get_db),
) -> MembershipRoleRepository:
    return MembershipRoleRepository(session)


# ── Service Dependency ──────────────────────────────────────────

async def get_authorization_service(
    role_repo: RoleRepository = Depends(get_role_repository),
    permission_repo: PermissionRepository = Depends(get_permission_repository),
    role_permission_repo: RolePermissionRepository = Depends(
        get_role_permission_repository,
    ),
    membership_role_repo: MembershipRoleRepository = Depends(
        get_membership_role_repository,
    ),
) -> AuthorizationService:
    return AuthorizationService(
        role_repo=role_repo,
        permission_repo=permission_repo,
        role_permission_repo=role_permission_repo,
        membership_role_repo=membership_role_repo,
    )


# ── Authorization Dependencies ──────────────────────────────────
# These integrate with Authentication (get_current_user) to provide
# permission-based access control for any endpoint.

async def get_current_permissions(
    current_user: CurrentUser = Depends(get_current_user),
    membership_id: uuid.UUID | None = None,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> CurrentPermissionsResponse:
    """
    Load all roles and permissions for the current user's membership.

    The membership_id should come from:
      - X-Membership-ID header (set by middleware)
      - First active membership for the user

    This is a building block for the permission-checking dependencies below.
    """
    if membership_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Membership ID required for permission check",
        )
    return await auth_service.get_current_permissions(membership_id)


def require_permission(permission_code: str) -> Callable:
    """
    FastAPI dependency that requires a specific permission.

    Usage:
        @router.get("/suppliers")
        async def list_suppliers(
            _: None = Depends(require_permission("supplier.read")),
        ):
            ...

    How it works:
        1. Authenticates the user via JWT (get_current_user)
        2. Resolves the membership from context
        3. Checks if the membership has the required permission
        4. Returns 403 if permission is missing
    """

    async def _dependency(
        current_user: CurrentUser = Depends(get_current_user),
        auth_service: AuthorizationService = Depends(get_authorization_service),
    ) -> None:
        membership_id = _resolve_membership_id()
        if membership_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active membership found",
            )
        granted = await auth_service.can(membership_id, permission_code)
        if not granted:
            raise PermissionDeniedError(permission_code)

    return _dependency


def require_any_permission(*permission_codes: str) -> Callable:
    """
    FastAPI dependency that requires at least one of the given permissions.

    Usage:
        @router.post("/purchases")
        async def create_purchase(
            _: None = Depends(
                require_any_permission("purchase.create", "purchase.approve")
            ),
        ):
            ...
    """

    async def _dependency(
        current_user: CurrentUser = Depends(get_current_user),
        auth_service: AuthorizationService = Depends(get_authorization_service),
    ) -> None:
        membership_id = _resolve_membership_id()
        if membership_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active membership found",
            )
        granted = await auth_service.can_any(membership_id, list(permission_codes))
        if not granted:
            raise PermissionDeniedError(
                f"any of ({', '.join(permission_codes)})",
            )

    return _dependency


def require_all_permissions(*permission_codes: str) -> Callable:
    """
    FastAPI dependency that requires ALL given permissions.

    Usage:
        @router.post("/organization/delete")
        async def delete_organization(
            _: None = Depends(
                require_all_permissions("organization.manage", "organization.delete")
            ),
        ):
            ...
    """

    async def _dependency(
        current_user: CurrentUser = Depends(get_current_user),
        auth_service: AuthorizationService = Depends(get_authorization_service),
    ) -> None:
        membership_id = _resolve_membership_id()
        if membership_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active membership found",
            )
        granted = await auth_service.can_all(membership_id, list(permission_codes))
        if not granted:
            missing = [
                c for c in permission_codes
                if not await auth_service.can(membership_id, c)
            ]
            raise PermissionDeniedError(f"all of ({', '.join(missing)})")

    return _dependency


# Decorator-based permission checks (for service methods)

def require_permission_decorator(permission_code: str) -> Callable:
    """Decorator for service methods that require a permission check."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # The service method should have access to auth_service and membership_id
            # This is a placeholder — actual integration depends on service design
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ── Internal helpers ────────────────────────────────────────────


def set_membership_id(membership_id: uuid.UUID) -> None:
    """Set the current membership ID in context."""
    MEMBERSHIP_ID_CONTEXT["current"] = membership_id


def _resolve_membership_id() -> uuid.UUID | None:
    """Resolve the current membership ID from context."""
    return MEMBERSHIP_ID_CONTEXT.get("current")

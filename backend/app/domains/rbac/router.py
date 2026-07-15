from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.domains.rbac.dependencies import get_authorization_service
from app.domains.rbac.exceptions import (
    DuplicatePermissionError,
    DuplicateRoleError,
    PermissionNotFoundError,
    RoleNotFoundError,
    SystemRoleModificationError,
)
from app.domains.rbac.schemas import (
    AssignPermissionRequest,
    AssignRoleRequest,
    BootstrapRequest,
    BootstrapResponse,
    CurrentPermissionsResponse,
    MembershipRoleResponse,
    PaginatedPermissionResponse,
    PaginatedRoleResponse,
    PermissionCheckRequest,
    PermissionCheckResponse,
    PermissionCreateRequest,
    PermissionResponse,
    PermissionUpdateRequest,
    RoleCreateRequest,
    RoleResponse,
    RoleSummary,
    RoleUpdateRequest,
)
from app.domains.rbac.service import AuthorizationService

router = APIRouter(prefix="/rbac", tags=["rbac"])


# ── Role Endpoints ──────────────────────────────────────────────


@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom role",
)
async def create_role(
    data: RoleCreateRequest,
    organization_id: uuid.UUID | None = Query(
        None, description="Organization ID (omit for global roles)",
    ),
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> RoleResponse:
    try:
        return await auth_service.create_role(data, organization_id)
    except DuplicateRoleError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.get(
    "/roles",
    response_model=PaginatedRoleResponse,
    summary="List all roles (system + organization-specific)",
)
async def list_roles(
    organization_id: uuid.UUID | None = Query(
        None, description="Filter by organization",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> PaginatedRoleResponse:
    return await auth_service.list_roles(
        organization_id=organization_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/roles/system",
    response_model=list[RoleSummary],
    summary="List all system roles",
)
async def list_system_roles(
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> list[RoleSummary]:
    return await auth_service.get_system_roles()


@router.get(
    "/roles/{role_id}",
    response_model=RoleResponse,
    summary="Get role details",
)
async def get_role(
    role_id: uuid.UUID,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> RoleResponse:
    try:
        return await auth_service.get_role(role_id)
    except RoleNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch(
    "/roles/{role_id}",
    response_model=RoleResponse,
    summary="Update a custom role",
)
async def update_role(
    role_id: uuid.UUID,
    data: RoleUpdateRequest,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> RoleResponse:
    try:
        return await auth_service.update_role(role_id, data)
    except RoleNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except SystemRoleModificationError as e:
        raise HTTPException(status_code=422, detail=e.message)


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a custom role",
)
async def delete_role(
    role_id: uuid.UUID,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> None:
    try:
        await auth_service.delete_role(role_id)
    except RoleNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except SystemRoleModificationError as e:
        raise HTTPException(status_code=422, detail=e.message)


# ── Permission Endpoints ────────────────────────────────────────


@router.post(
    "/permissions",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new permission",
)
async def create_permission(
    data: PermissionCreateRequest,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> PermissionResponse:
    try:
        return await auth_service.create_permission(data)
    except DuplicatePermissionError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.get(
    "/permissions",
    response_model=PaginatedPermissionResponse,
    summary="List all permissions",
)
async def list_permissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = Query(None, description="Filter by category"),
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> PaginatedPermissionResponse:
    return await auth_service.list_permissions(
        page=page, page_size=page_size, category=category,
    )


@router.get(
    "/permissions/search",
    response_model=PaginatedPermissionResponse,
    summary="Search permissions by code, resource, or description",
)
async def search_permissions(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> PaginatedPermissionResponse:
    return await auth_service.search_permissions(
        query_str=q, page=page, page_size=page_size,
    )


@router.get(
    "/permissions/{permission_id}",
    response_model=PermissionResponse,
    summary="Get permission details",
)
async def get_permission(
    permission_id: uuid.UUID,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> PermissionResponse:
    try:
        return await auth_service.get_permission(permission_id)
    except PermissionNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch(
    "/permissions/{permission_id}",
    response_model=PermissionResponse,
    summary="Update permission metadata",
)
async def update_permission(
    permission_id: uuid.UUID,
    data: PermissionUpdateRequest,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> PermissionResponse:
    try:
        return await auth_service.update_permission(permission_id, data)
    except PermissionNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete(
    "/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a permission",
)
async def delete_permission(
    permission_id: uuid.UUID,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> None:
    try:
        await auth_service.delete_permission(permission_id)
    except PermissionNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


# ── Role-Permission Assignment ──────────────────────────────────


@router.post(
    "/roles/{role_id}/permissions",
    response_model=list[uuid.UUID],
    summary="Assign permissions to a role",
)
async def assign_permissions_to_role(
    role_id: uuid.UUID,
    data: AssignPermissionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> list[uuid.UUID]:
    try:
        return await auth_service.assign_permissions_to_role(
            role_id, data, granted_by=current_user.id,
        )
    except RoleNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete(
    "/roles/{role_id}/permissions",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove permissions from a role",
)
async def remove_permissions_from_role(
    role_id: uuid.UUID,
    data: AssignPermissionRequest,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> None:
    try:
        await auth_service.remove_permissions_from_role(
            role_id, data.permission_ids,
        )
    except RoleNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get(
    "/roles/{role_id}/permissions",
    response_model=list[uuid.UUID],
    summary="Get permission IDs for a role",
)
async def get_role_permissions(
    role_id: uuid.UUID,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> list[uuid.UUID]:
    return await auth_service.get_role_permission_ids(role_id)


# ── Membership-Role Assignment ──────────────────────────────────


@router.post(
    "/memberships/{membership_id}/roles",
    response_model=list[MembershipRoleResponse],
    summary="Assign roles to a membership",
)
async def assign_roles_to_membership(
    membership_id: uuid.UUID,
    data: AssignRoleRequest,
    current_user: CurrentUser = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> list[MembershipRoleResponse]:
    return await auth_service.assign_roles_to_membership(
        membership_id, data, assigned_by=current_user.id,
    )


@router.get(
    "/memberships/{membership_id}/roles",
    response_model=list[MembershipRoleResponse],
    summary="Get all roles for a membership",
)
async def get_membership_roles(
    membership_id: uuid.UUID,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> list[MembershipRoleResponse]:
    return await auth_service.get_membership_roles(membership_id)


@router.delete(
    "/memberships/{membership_id}/roles",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove roles from a membership",
)
async def remove_roles_from_membership(
    membership_id: uuid.UUID,
    data: AssignRoleRequest,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> None:
    await auth_service.remove_roles_from_membership(
        membership_id, data.role_ids,
    )


# ── Authorization Check Endpoints ───────────────────────────────


@router.post(
    "/check/{membership_id}",
    response_model=PermissionCheckResponse,
    summary="Check if a membership has specific permissions",
)
async def check_permissions(
    membership_id: uuid.UUID,
    data: PermissionCheckRequest,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> PermissionCheckResponse:
    return await auth_service.check_permissions(membership_id, data)


@router.get(
    "/permissions/{membership_id}",
    response_model=CurrentPermissionsResponse,
    summary="Get all current permissions for a membership",
)
async def get_current_permissions(
    membership_id: uuid.UUID,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> CurrentPermissionsResponse:
    return await auth_service.get_current_permissions(membership_id)


# ── Bootstrap Endpoints ──────────────────────────────────────────


@router.post(
    "/bootstrap",
    response_model=BootstrapResponse,
    summary="Bootstrap authorization for a new organization",
)
async def bootstrap_organization(
    data: BootstrapRequest,
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> BootstrapResponse:
    return await auth_service.bootstrap_organization(data)


@router.post(
    "/seed",
    status_code=status.HTTP_200_OK,
    summary="Seed system roles and permissions (idempotent)",
)
async def seed_system_roles(
    auth_service: AuthorizationService = Depends(get_authorization_service),
) -> dict[str, str]:
    await auth_service.seed_system_roles()
    return {"message": "System roles and permissions seeded successfully"}

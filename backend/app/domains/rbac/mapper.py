from __future__ import annotations

from app.domains.rbac.models import MembershipRole, Permission, Role, RolePermission
from app.domains.rbac.schemas import (
    MembershipRoleResponse,
    PermissionResponse,
    PermissionSummary,
    RolePermissionResponse,
    RoleResponse,
    RoleSummary,
)


class RoleMapper:
    @staticmethod
    def to_response(role: Role) -> RoleResponse:
        metadata = None if role.metadata_ is None else role.metadata_
        return RoleResponse(
            id=role.id,
            organization_id=role.organization_id,
            name=role.name,
            slug=role.slug,
            description=role.description,
            is_system_role=role.is_system_role,
            priority=role.priority,
            metadata=metadata,
            created_at=role.created_at,
            updated_at=role.updated_at,
        )

    @staticmethod
    def to_summary(role: Role) -> RoleSummary:
        return RoleSummary.model_validate(role)

    @staticmethod
    def to_response_list(roles: list[Role]) -> list[RoleResponse]:
        return [RoleMapper.to_response(r) for r in roles]


class PermissionMapper:
    @staticmethod
    def to_response(perm: Permission) -> PermissionResponse:
        metadata = None if perm.metadata_ is None else perm.metadata_
        return PermissionResponse(
            id=perm.id,
            resource=perm.resource,
            action=perm.action,
            code=perm.code,
            description=perm.description,
            category=perm.category,
            is_system_permission=perm.is_system_permission,
            metadata=metadata,
            created_at=perm.created_at,
            updated_at=perm.updated_at,
        )

    @staticmethod
    def to_summary(perm: Permission) -> PermissionSummary:
        return PermissionSummary.model_validate(perm)

    @staticmethod
    def to_response_list(perms: list[Permission]) -> list[PermissionResponse]:
        return [PermissionMapper.to_response(p) for p in perms]


class RolePermissionMapper:
    @staticmethod
    def to_response(rp: RolePermission) -> RolePermissionResponse:
        return RolePermissionResponse.model_validate(rp)


class MembershipRoleMapper:
    @staticmethod
    def to_response(mr: MembershipRole) -> MembershipRoleResponse:
        resp = MembershipRoleResponse.model_validate(mr)
        if mr.role:
            resp.role_name = mr.role.name
        return resp

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from loguru import logger

from app.domains.rbac.mapper import (
    MembershipRoleMapper,
    PermissionMapper,
    RoleMapper,
)
from app.domains.rbac.models import Permission, Role, RolePermission
from app.domains.rbac.repository import (
    MembershipRoleRepository,
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
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
from app.domains.rbac.validators import (
    check_duplicate_permission,
    check_duplicate_role,
    check_permission_exists,
    check_role_exists,
    ensure_not_system_role,
    validate_permission_code,
    validate_permission_update_data,
    validate_role_assignment_data,
    validate_slug,
)
from app.repositories.pagination import Pagination


class AuthorizationService:
    """
    Central authorization service for the entire Procura AI platform.

    Responsibilities:
      1. Role management (CRUD, system role protection)
      2. Permission management (CRUD, code uniqueness)
      3. Role-Permission assignment (grant/revoke)
      4. Membership-Role assignment (grant/revoke)
      5. Authorization checks (can, can_any, can_all)
      6. Permission caching hooks (future Redis integration)
      7. Future ABAC/Policy engine integration points
      8. Future AI authorization integration points

    Every future module calls this service. They never bypass it.
    """

    def __init__(
        self,
        role_repo: RoleRepository,
        permission_repo: PermissionRepository,
        role_permission_repo: RolePermissionRepository,
        membership_role_repo: MembershipRoleRepository,
    ) -> None:
        self._role_repo = role_repo
        self._perm_repo = permission_repo
        self._rp_repo = role_permission_repo
        self._mr_repo = membership_role_repo

    # ── Role Management ─────────────────────────────────────────

    async def create_role(
        self,
        data: RoleCreateRequest,
        organization_id: uuid.UUID | None = None,
    ) -> RoleResponse:
        validated = validate_role_assignment_data(data.model_dump())
        name: str = validated["name"]
        slug: str = validated.get("slug", validate_slug(name))

        existing = await self._role_repo.find_by_slug(slug, organization_id)
        check_duplicate_role(existing, name=name, slug=slug)

        existing_name = await self._role_repo.find_by_name(name, organization_id)
        check_duplicate_role(existing_name, name=name)

        role = Role(
            organization_id=organization_id,
            name=name,
            slug=slug,
            description=validated.get("description"),
            is_system_role=False,
            priority=validated.get("priority", 0),
        )
        if "metadata" in validated:
            role.metadata_ = validated["metadata"]

        self._role_repo.session.add(role)
        await self._role_repo.session.flush()
        await self._role_repo.session.refresh(role)

        logger.info("Role created", role_id=str(role.id), name=name, slug=slug)

        return RoleMapper.to_response(role)

    async def get_role(self, role_id: uuid.UUID) -> RoleResponse:
        role = await self._role_repo.get_by_id(role_id)
        role = check_role_exists(role, str(role_id))
        return RoleMapper.to_response(role)

    async def update_role(
        self, role_id: uuid.UUID, data: RoleUpdateRequest,
    ) -> RoleResponse:
        role = await self._role_repo.get_by_id(role_id)
        role = check_role_exists(role, str(role_id))
        ensure_not_system_role(role, "update")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "metadata":
                setattr(role, "metadata_", value)
            elif value is not None:
                setattr(role, key, value)

        await self._role_repo.session.flush()
        await self._role_repo.session.refresh(role)

        logger.info("Role updated", role_id=str(role_id))

        return RoleMapper.to_response(role)

    async def delete_role(self, role_id: uuid.UUID) -> None:
        role = await self._role_repo.get_by_id(role_id)
        role = check_role_exists(role, str(role_id))
        ensure_not_system_role(role, "delete")
        await self._role_repo.soft_delete(role_id)

        logger.info("Role deleted", role_id=str(role_id))

    async def list_roles(
        self,
        organization_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedRoleResponse:
        pagination = Pagination.from_page(page, page_size)
        result = await self._role_repo.list_by_organization(
            organization_id, pagination=pagination,
        )
        items = RoleMapper.to_response_list(result.items)
        total_pages = max(1, (result.total + page_size - 1) // page_size)
        return PaginatedRoleResponse(
            items=items,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=total_pages,
        )

    async def get_system_roles(self) -> list[RoleSummary]:
        roles = await self._role_repo.get_system_roles()
        return [RoleMapper.to_summary(r) for r in roles]

    # ── Permission Management ───────────────────────────────────

    async def create_permission(
        self, data: PermissionCreateRequest,
    ) -> PermissionResponse:
        code = validate_permission_code(data.resource, data.action)
        existing = await self._perm_repo.find_by_code(code)
        check_duplicate_permission(existing, code)

        perm = Permission(
            resource=data.resource,
            action=data.action,
            code=code,
            description=data.description,
            category=data.category,
            is_system_permission=False,
        )
        if data.metadata:
            perm.metadata_ = data.metadata

        self._perm_repo.session.add(perm)
        await self._perm_repo.session.flush()
        await self._perm_repo.session.refresh(perm)

        logger.info("Permission created", code=code, perm_id=str(perm.id))

        return PermissionMapper.to_response(perm)

    async def get_permission(self, permission_id: uuid.UUID) -> PermissionResponse:
        perm = await self._perm_repo.get_by_id(permission_id)
        perm = check_permission_exists(perm, str(permission_id))
        return PermissionMapper.to_response(perm)

    async def update_permission(
        self, permission_id: uuid.UUID, data: PermissionUpdateRequest,
    ) -> PermissionResponse:
        perm = await self._perm_repo.get_by_id(permission_id)
        perm = check_permission_exists(perm, str(permission_id))

        update_data = validate_permission_update_data(data.model_dump(exclude_unset=True))
        for key, value in update_data.items():
            if key == "metadata":
                setattr(perm, "metadata_", value)
            elif value is not None:
                setattr(perm, key, value)

        await self._perm_repo.session.flush()
        await self._perm_repo.session.refresh(perm)
        return PermissionMapper.to_response(perm)

    async def delete_permission(self, permission_id: uuid.UUID) -> None:
        perm = await self._perm_repo.get_by_id(permission_id)
        perm = check_permission_exists(perm, str(permission_id))
        if perm.is_system_permission:
            from app.domains.rbac.exceptions import SystemRoleModificationError
            raise SystemRoleModificationError(
                action="delete", role_name=perm.code,
            )
        await self._perm_repo.soft_delete(permission_id)

    async def list_permissions(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
    ) -> PaginatedPermissionResponse:
        if category:
            pagination = Pagination.from_page(page, page_size)
            result = await self._perm_repo.list_by_category(
                category, pagination=pagination,
            )
        else:
            pagination = Pagination.from_page(page, page_size)
            result = await self._perm_repo.list(
                pagination=pagination,
            )
        items = PermissionMapper.to_response_list(result.items)
        total_pages = max(1, (result.total + page_size - 1) // page_size)
        return PaginatedPermissionResponse(
            items=items,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=total_pages,
        )

    async def search_permissions(
        self, query_str: str, page: int = 1, page_size: int = 20,
    ) -> PaginatedPermissionResponse:
        pagination = Pagination.from_page(page, page_size)
        result = await self._perm_repo.search(query_str, pagination=pagination)
        items = PermissionMapper.to_response_list(result.items)
        total_pages = max(1, (result.total + page_size - 1) // page_size)
        return PaginatedPermissionResponse(
            items=items,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=total_pages,
        )

    # ── Role-Permission Assignment ──────────────────────────────

    async def assign_permissions_to_role(
        self,
        role_id: uuid.UUID,
        data: AssignPermissionRequest,
        granted_by: uuid.UUID | None = None,
    ) -> list[uuid.UUID]:
        role = await self._role_repo.get_by_id(role_id)
        check_role_exists(role, str(role_id))
        ensure_not_system_role(role, "modify permissions of")

        results = await self._rp_repo.assign_many(
            role_id, data.permission_ids, granted_by,
        )
        assigned_ids = [rp.permission_id for rp in results]

        logger.info(
            "Permissions assigned to role",
            role_id=str(role_id),
            count=len(assigned_ids),
        )

        return assigned_ids

    async def remove_permissions_from_role(
        self,
        role_id: uuid.UUID,
        permission_ids: list[uuid.UUID],
    ) -> None:
        role = await self._role_repo.get_by_id(role_id)
        check_role_exists(role, str(role_id))
        ensure_not_system_role(role, "modify permissions of")

        await self._rp_repo.remove_many(role_id, permission_ids)

        logger.info(
            "Permissions removed from role",
            role_id=str(role_id),
            count=len(permission_ids),
        )

    async def get_role_permission_ids(
        self, role_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        return await self._rp_repo.get_permission_ids_for_role(role_id)

    async def get_role_permission_codes(self, role_id: uuid.UUID) -> list[str]:
        return await self._rp_repo.get_permission_codes_for_role(role_id)

    # ── Membership-Role Assignment ──────────────────────────────

    async def assign_roles_to_membership(
        self,
        membership_id: uuid.UUID,
        data: AssignRoleRequest,
        assigned_by: uuid.UUID | None = None,
    ) -> list[MembershipRoleResponse]:
        results = await self._mr_repo.assign_many(
            membership_id, data.role_ids, assigned_by, data.expires_at,
        )

        logger.info(
            "Roles assigned to membership",
            membership_id=str(membership_id),
            count=len(data.role_ids),
        )

        return [MembershipRoleMapper.to_response(mr) for mr in results]

    async def remove_roles_from_membership(
        self,
        membership_id: uuid.UUID,
        role_ids: list[uuid.UUID],
    ) -> None:
        await self._mr_repo.remove_many(membership_id, role_ids)

        logger.info(
            "Roles removed from membership",
            membership_id=str(membership_id),
            count=len(role_ids),
        )

    async def get_membership_roles(
        self, membership_id: uuid.UUID,
    ) -> list[MembershipRoleResponse]:
        mrs = await self._mr_repo.list_by_membership(membership_id)
        return [MembershipRoleMapper.to_response(mr) for mr in mrs]

    async def get_membership_role_ids(
        self, membership_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        return await self._mr_repo.get_role_ids_for_membership(membership_id)

    # ── Authorization Checks ────────────────────────────────────

    async def can(
        self, membership_id: uuid.UUID, permission_code: str,
    ) -> bool:
        """
        Check if a membership has a specific permission.

        This is the core authorization check. Every endpoint in the
        system calls this (directly or via dependencies).

        Future: this method will check:
          1. RBAC permissions (current implementation)
          2. ABAC rules (contextual: time, location, device)
          3. Policy engine (custom policies per organization)
          4. AI authorization (AI evaluates if the action is safe)

        Future caching: Redis cache key = f"perm:{membership_id}:{permission_code}"
        """
        return await self._mr_repo.has_permission(membership_id, permission_code)

    async def can_any(
        self, membership_id: uuid.UUID, permission_codes: list[str],
    ) -> bool:
        """Check if a membership has ANY of the given permissions."""
        return await self._mr_repo.has_any_permission(membership_id, permission_codes)

    async def can_all(
        self, membership_id: uuid.UUID, permission_codes: list[str],
    ) -> bool:
        """Check if a membership has ALL of the given permissions."""
        return await self._mr_repo.has_all_permissions(membership_id, permission_codes)

    async def check_permission(
        self, membership_id: uuid.UUID, permission_code: str,
    ) -> PermissionCheckResponse:
        """Check a permission and return a structured response."""
        granted = await self.can(membership_id, permission_code)
        return PermissionCheckResponse(
            granted=granted,
            missing_permissions=[] if granted else [permission_code],
        )

    async def check_permissions(
        self, membership_id: uuid.UUID, data: PermissionCheckRequest,
    ) -> PermissionCheckResponse:
        """Check multiple permissions and return which are missing."""
        granted = await self.can_all(membership_id, data.permission_codes)
        if granted:
            return PermissionCheckResponse(granted=True)

        perms = await self._mr_repo.get_all_permissions_for_membership(membership_id)
        missing = [c for c in data.permission_codes if c not in perms]
        return PermissionCheckResponse(granted=False, missing_permissions=missing)

    async def get_current_permissions(
        self, membership_id: uuid.UUID,
    ) -> CurrentPermissionsResponse:
        """Get all roles and permissions for a membership."""
        mrs = await self._mr_repo.get_active_roles_for_membership(membership_id)
        role_ids = [mr.role_id for mr in mrs]
        role_names = [mr.role.name for mr in mrs if mr.role]
        permission_codes = list(
            await self._mr_repo.get_all_permissions_for_membership(membership_id),
        )
        return CurrentPermissionsResponse(
            membership_id=membership_id,
            role_ids=role_ids,
            role_names=role_names,
            permission_codes=sorted(permission_codes),
        )

    async def get_all_permissions_for_membership(
        self, membership_id: uuid.UUID,
    ) -> set[str]:
        """Get the full set of permission codes for a membership."""
        return await self._mr_repo.get_all_permissions_for_membership(membership_id)

    # ── Bootstrap ───────────────────────────────────────────────

    async def bootstrap_organization(
        self, data: BootstrapRequest,
    ) -> BootstrapResponse:
        """
        Bootstrap authorization for a new organization.

        Called when an organization is created. Assigns the Owner role
        to the founding user. The Owner role must exist as a system role.

        Future: this will also create default org-specific roles based
        on the organization's subscription plan and industry.
        """
        role = await self._role_repo.find_by_slug(data.role_slug)
        if role is None:
            raise ValueError(
                f"System role '{data.role_slug}' not found. "
                "Run system bootstrapping first.",
            )

        mr = await self._mr_repo.assign(
            membership_id=data.user_id,
            role_id=role.id,
        )

        logger.info(
            "Organization bootstrapped with owner role",
            organization_id=str(data.organization_id),
            membership_id=str(data.user_id),
            role_id=str(role.id),
        )

        return BootstrapResponse(
            role_id=role.id,
            membership_role_id=mr.id,
            message="Organization bootstrapped with Owner role",
        )

    async def seed_system_roles(self) -> None:
        """
        Seed the database with system roles and permissions.

        Called once during initial deployment or migration.
        Idempotent: skips roles/permissions that already exist.
        """
        from app.domains.rbac.enums import PermissionCategory

        # Define system roles
        system_roles = [
            {
                "name": "Owner",
                "slug": "owner",
                "description": "Full access to all organization resources and settings",
                "priority": 100,
                "permission_codes": ["*"],  # Wildcard: all permissions
            },
            {
                "name": "Admin",
                "slug": "admin",
                "description": (
                    "Full administrative access except billing and org deletion"
                ),
                "priority": 80,
                "permission_codes": [
                    "organization.read", "organization.update",
                    "user.create", "user.read", "user.update",
                    "membership.create", "membership.read",
                    "membership.update", "membership.delete",
                    "role.create", "role.read", "role.update", "role.delete",
                    "purchase.read", "supplier.read", "contract.read",
                    "invoice.read", "document.read",
                ],
            },
            {
                "name": "Procurement Manager",
                "slug": "procurement_manager",
                "description": "Full procurement lifecycle management",
                "priority": 60,
                "permission_codes": [
                    "organization.read",
                    "user.read",
                    "supplier.create", "supplier.read",
                    "supplier.update", "supplier.delete",
                    "contract.create", "contract.read",
                    "contract.update",
                    "purchase.create", "purchase.read",
                    "purchase.update", "purchase.approve",
                    "invoice.read", "invoice.approve",
                    "document.upload", "document.read",
                ],
            },
            {
                "name": "Procurement Analyst",
                "slug": "procurement_analyst",
                "description": "Read-only access to procurement data for analysis",
                "priority": 40,
                "permission_codes": [
                    "organization.read",
                    "user.read",
                    "supplier.read",
                    "contract.read",
                    "purchase.read",
                    "invoice.read",
                    "document.read",
                ],
            },
            {
                "name": "Finance Approver",
                "slug": "finance_approver",
                "description": "Financial approval for purchases and invoices",
                "priority": 50,
                "permission_codes": [
                    "organization.read",
                    "user.read",
                    "supplier.read",
                    "contract.read",
                    "purchase.read", "purchase.approve",
                    "invoice.read", "invoice.approve",
                    "document.read",
                ],
            },
            {
                "name": "Viewer",
                "slug": "viewer",
                "description": "Read-only access to non-sensitive data",
                "priority": 10,
                "permission_codes": [
                    "organization.read",
                    "purchase.read",
                    "supplier.read",
                    "contract.read",
                    "invoice.read",
                    "document.read",
                ],
            },
        ]

        # Create system roles (without permissions first)
        created_roles: dict[str, Role] = {}
        for role_def in system_roles:
            existing = await self._role_repo.find_by_slug(role_def["slug"])
            if existing:
                created_roles[role_def["slug"]] = existing
                continue

            role = Role(
                organization_id=None,
                name=role_def["name"],
                slug=role_def["slug"],
                description=role_def["description"],
                is_system_role=True,
                priority=role_def["priority"],
            )
            self._role_repo.session.add(role)
            await self._role_repo.session.flush()
            await self._role_repo.session.refresh(role)
            created_roles[role_def["slug"]] = role

        # Create standard permissions
        standard_permissions = self._get_standard_permissions()

        created_perms: dict[str, Permission] = {}
        for perm_def in standard_permissions:
            code = validate_permission_code(perm_def["resource"], perm_def["action"])
            existing = await self._perm_repo.find_by_code(code)
            if existing:
                created_perms[code] = existing
                continue

            perm = Permission(
                resource=perm_def["resource"],
                action=perm_def["action"],
                code=code,
                description=perm_def["description"],
                category=PermissionCategory(perm_def["category"]),
                is_system_permission=True,
            )
            self._perm_repo.session.add(perm)
            await self._perm_repo.session.flush()
            await self._perm_repo.session.refresh(perm)
            created_perms[code] = perm

        # Assign permissions to roles (skip Owner — it gets all via wildcard)
        for role_def in system_roles:
            if role_def["slug"] == "owner":
                continue
            role = created_roles.get(role_def["slug"])
            if not role:
                continue
            for code in role_def["permission_codes"]:
                perm = created_perms.get(code)
                if not perm:
                    continue
                existing_rp = await self._rp_repo.get_by_role_and_permission(
                    role.id, perm.id,
                )
                if not existing_rp:
                    rp = RolePermission(
                        role_id=role.id,
                        permission_id=perm.id,
                        granted_at=datetime.now(UTC),
                    )
                    self._rp_repo.session.add(rp)

        await self._rp_repo.session.flush()

        logger.info(
            "System roles and permissions seeded",
            roles=len(created_roles),
            permissions=len(created_perms),
        )

    def _get_standard_permissions(self) -> list[dict]:
        return [
            # ── Organization ──
            {"resource": "organization", "action": "manage",
             "description": "Full organization management", "category": "organization"},
            {"resource": "organization", "action": "read",
             "description": "View organization details", "category": "organization"},
            {"resource": "organization", "action": "update",
             "description": "Update organization settings", "category": "organization"},
            {"resource": "organization", "action": "delete",
             "description": "Delete organization", "category": "organization"},
            # ── User ──
            {"resource": "user", "action": "create",
             "description": "Create new users", "category": "user"},
            {"resource": "user", "action": "read",
             "description": "View user details", "category": "user"},
            {"resource": "user", "action": "update",
             "description": "Update user details", "category": "user"},
            {"resource": "user", "action": "delete",
             "description": "Delete users", "category": "user"},
            # ── Membership ──
            {"resource": "membership", "action": "create",
             "description": "Invite members", "category": "membership"},
            {"resource": "membership", "action": "read",
             "description": "View members", "category": "membership"},
            {"resource": "membership", "action": "update",
             "description": "Update member roles/status", "category": "membership"},
            {"resource": "membership", "action": "delete",
             "description": "Remove members", "category": "membership"},
            # ── Role ──
            {"resource": "role", "action": "create",
             "description": "Create custom roles", "category": "role"},
            {"resource": "role", "action": "read",
             "description": "View roles", "category": "role"},
            {"resource": "role", "action": "update",
             "description": "Update roles", "category": "role"},
            {"resource": "role", "action": "delete",
             "description": "Delete custom roles", "category": "role"},
            {"resource": "role", "action": "assign",
             "description": "Assign roles to members", "category": "role"},
            # ── Supplier (future) ──
            {"resource": "supplier", "action": "create",
             "description": "Create suppliers", "category": "supplier"},
            {"resource": "supplier", "action": "read",
             "description": "View suppliers", "category": "supplier"},
            {"resource": "supplier", "action": "update",
             "description": "Update suppliers", "category": "supplier"},
            {"resource": "supplier", "action": "delete",
             "description": "Delete suppliers", "category": "supplier"},
            # ── Contract (future) ──
            {"resource": "contract", "action": "create",
             "description": "Create contracts", "category": "contract"},
            {"resource": "contract", "action": "read",
             "description": "View contracts", "category": "contract"},
            {"resource": "contract", "action": "update",
             "description": "Update contracts", "category": "contract"},
            {"resource": "contract", "action": "delete",
             "description": "Delete contracts", "category": "contract"},
            # ── Purchase ──
            {"resource": "purchase", "action": "create",
             "description": "Create purchase requests", "category": "purchase"},
            {"resource": "purchase", "action": "read",
             "description": "View purchase requests/orders", "category": "purchase"},
            {"resource": "purchase", "action": "update",
             "description": "Update purchase requests/orders", "category": "purchase"},
            {"resource": "purchase", "action": "delete",
             "description": "Delete purchase requests/orders", "category": "purchase"},
            {"resource": "purchase", "action": "approve",
             "description": "Approve purchase requests/orders",
             "category": "purchase"},
            # ── Invoice ──
            {"resource": "invoice", "action": "read",
             "description": "View invoices", "category": "invoice"},
            {"resource": "invoice", "action": "approve",
             "description": "Approve invoices", "category": "invoice"},
            {"resource": "invoice", "action": "delete",
             "description": "Delete invoices", "category": "invoice"},
            # ── Document ──
            {"resource": "document", "action": "upload",
             "description": "Upload documents", "category": "document"},
            {"resource": "document", "action": "read",
             "description": "Read/download documents", "category": "document"},
            {"resource": "document", "action": "delete",
             "description": "Delete documents", "category": "document"},
            # ── System ──
            {"resource": "system", "action": "manage",
             "description": "System administration", "category": "system"},
            {"resource": "system", "action": "read",
             "description": "Read system settings/audit logs", "category": "system"},
        ]

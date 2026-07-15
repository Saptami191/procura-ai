from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.domains.rbac.models import MembershipRole, Permission, Role, RolePermission
from app.repositories.base import BaseRepository
from app.repositories.pagination import Page, Pagination


class RoleRepository(BaseRepository[Role, uuid.UUID]):
    model = Role

    async def find_by_slug(
        self, slug: str, organization_id: uuid.UUID | None = None,
        *,
        include_deleted: bool = False,
    ) -> Role | None:
        query = select(Role).where(Role.slug == slug)
        if organization_id:
            query = query.where(Role.organization_id == organization_id)
        else:
            query = query.where(Role.organization_id.is_(None))
        query = self._apply_soft_delete_filter(query, include_deleted)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def find_by_name(
        self, name: str, organization_id: uuid.UUID | None = None,
        *,
        include_deleted: bool = False,
    ) -> Role | None:
        query = select(Role).where(Role.name == name)
        if organization_id:
            query = query.where(Role.organization_id == organization_id)
        else:
            query = query.where(Role.organization_id.is_(None))
        query = self._apply_soft_delete_filter(query, include_deleted)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_by_organization(
        self,
        organization_id: uuid.UUID | None = None,
        *,
        include_system: bool = True,
        pagination: Pagination | None = None,
    ) -> Page[Role]:
        conditions = []
        if organization_id:
            conditions.append(
                or_(
                    Role.organization_id == organization_id,
                    Role.organization_id.is_(None),
                ),
            )
        if not include_system:
            conditions.append(Role.is_system_role.is_(False))

        query = select(Role)
        if conditions:
            query = query.where(and_(*conditions))
        query = self._apply_soft_delete_filter(query, False)
        query = query.order_by(Role.priority.desc(), Role.name.asc())

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        if pagination:
            query = pagination.apply(query)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        page = pagination.page if pagination else 1
        page_size = pagination.limit if pagination else max(total, 1) if total > 0 else 1

        return Page(items=items, total=total, page=page, page_size=page_size)

    async def get_system_roles(self) -> list[Role]:
        query = select(Role).where(
            Role.is_system_role.is_(True),
            Role.is_deleted.is_(False),
        ).order_by(Role.priority.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_org_roles(
        self, organization_id: uuid.UUID,
    ) -> list[Role]:
        query = (
            select(Role)
            .where(
                Role.organization_id == organization_id,
                Role.is_deleted.is_(False),
            )
            .order_by(Role.name.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class PermissionRepository(BaseRepository[Permission, uuid.UUID]):
    model = Permission

    async def find_by_code(
        self, code: str, *, include_deleted: bool = False,
    ) -> Permission | None:
        query = select(Permission).where(Permission.code == code)
        query = self._apply_soft_delete_filter(query, include_deleted)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def find_by_codes(
        self, codes: list[str], *, include_deleted: bool = False,
    ) -> list[Permission]:
        query = select(Permission).where(Permission.code.in_(codes))
        query = self._apply_soft_delete_filter(query, include_deleted)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_category(
        self, category: str, *, pagination: Pagination | None = None,
    ) -> Page[Permission]:
        query = (
            select(Permission)
            .where(
                Permission.category == category,
                Permission.is_deleted.is_(False),
            )
            .order_by(Permission.resource.asc(), Permission.action.asc())
        )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        if pagination:
            query = pagination.apply(query)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        page = pagination.page if pagination else 1
        page_size = pagination.limit if pagination else max(total, 1) if total > 0 else 1

        return Page(items=items, total=total, page=page, page_size=page_size)

    async def list_by_resource(self, resource: str) -> list[Permission]:
        query = (
            select(Permission)
            .where(
                Permission.resource == resource,
                Permission.is_deleted.is_(False),
            )
            .order_by(Permission.action.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search(
        self, query_str: str, *, pagination: Pagination | None = None,
    ) -> Page[Permission]:
        pattern = f"%{query_str}%"
        filters = or_(
            Permission.code.ilike(pattern),
            Permission.resource.ilike(pattern),
            Permission.description.ilike(pattern),
        )

        base_query = (
            select(Permission)
            .where(filters, Permission.is_deleted.is_(False))
            .order_by(Permission.resource.asc(), Permission.action.asc())
        )

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        query = base_query
        if pagination:
            query = pagination.apply(query)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        page = pagination.page if pagination else 1
        page_size = pagination.limit if pagination else max(total, 1) if total > 0 else 1

        return Page(items=items, total=total, page=page, page_size=page_size)


class RolePermissionRepository(BaseRepository[RolePermission, uuid.UUID]):
    model = RolePermission

    async def assign(
        self,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
        granted_by: uuid.UUID | None = None,
    ) -> RolePermission:
        existing = await self.get_by_role_and_permission(role_id, permission_id)
        if existing:
            return existing

        rp = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
            granted_by=granted_by,
            granted_at=datetime.now(UTC),
        )
        self.session.add(rp)
        await self.session.flush()
        await self.session.refresh(rp)
        return rp

    async def assign_many(
        self,
        role_id: uuid.UUID,
        permission_ids: list[uuid.UUID],
        granted_by: uuid.UUID | None = None,
    ) -> list[RolePermission]:
        results: list[RolePermission] = []
        for pid in permission_ids:
            rp = await self.assign(role_id, pid, granted_by)
            results.append(rp)
        return results

    async def remove(
        self, role_id: uuid.UUID, permission_id: uuid.UUID,
    ) -> None:
        rp = await self.get_by_role_and_permission(role_id, permission_id)
        if rp:
            await self.session.delete(rp)
            await self.session.flush()

    async def remove_many(
        self, role_id: uuid.UUID, permission_ids: list[uuid.UUID],
    ) -> None:
        query = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id.in_(permission_ids),
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        for item in items:
            await self.session.delete(item)
        await self.session.flush()

    async def get_by_role_and_permission(
        self, role_id: uuid.UUID, permission_id: uuid.UUID,
    ) -> RolePermission | None:
        query = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_permission_ids_for_role(
        self, role_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        query = select(RolePermission.permission_id).where(
            RolePermission.role_id == role_id,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_permission_codes_for_role(self, role_id: uuid.UUID) -> list[str]:
        query = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id == role_id,
                Permission.is_deleted.is_(False),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_permission_codes_for_roles(
        self, role_ids: list[uuid.UUID],
    ) -> set[str]:
        if not role_ids:
            return set()
        query = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id.in_(role_ids),
                Permission.is_deleted.is_(False),
            )
        )
        result = await self.session.execute(query)
        return set(result.scalars().all())

    async def has_permission(
        self, role_id: uuid.UUID, permission_code: str,
    ) -> bool:
        query = (
            select(RolePermission.id)
            .join(Permission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id == role_id,
                Permission.code == permission_code,
                Permission.is_deleted.is_(False),
            )
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalars().first() is not None


class MembershipRoleRepository(BaseRepository[MembershipRole, uuid.UUID]):
    model = MembershipRole

    async def assign(
        self,
        membership_id: uuid.UUID,
        role_id: uuid.UUID,
        assigned_by: uuid.UUID | None = None,
        expires_at: datetime | None = None,
    ) -> MembershipRole:
        existing = await self.get_by_membership_and_role(membership_id, role_id)
        if existing:
            if existing.is_deleted:
                await self.restore(existing.id)
            return existing

        mr = MembershipRole(
            membership_id=membership_id,
            role_id=role_id,
            assigned_by=assigned_by,
            assigned_at=datetime.now(UTC),
            expires_at=expires_at,
        )
        self.session.add(mr)
        await self.session.flush()
        await self.session.refresh(mr)
        return mr

    async def assign_many(
        self,
        membership_id: uuid.UUID,
        role_ids: list[uuid.UUID],
        assigned_by: uuid.UUID | None = None,
        expires_at: datetime | None = None,
    ) -> list[MembershipRole]:
        results: list[MembershipRole] = []
        for rid in role_ids:
            mr = await self.assign(membership_id, rid, assigned_by, expires_at)
            results.append(mr)
        return results

    async def remove(
        self, membership_id: uuid.UUID, role_id: uuid.UUID,
    ) -> None:
        mr = await self.get_by_membership_and_role(membership_id, role_id)
        if mr:
            await self.soft_delete(mr.id)

    async def remove_many(
        self, membership_id: uuid.UUID, role_ids: list[uuid.UUID],
    ) -> None:
        for rid in role_ids:
            await self.remove(membership_id, rid)

    async def get_by_membership_and_role(
        self, membership_id: uuid.UUID, role_id: uuid.UUID,
    ) -> MembershipRole | None:
        query = select(MembershipRole).where(
            MembershipRole.membership_id == membership_id,
            MembershipRole.role_id == role_id,
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_active_roles_for_membership(
        self, membership_id: uuid.UUID,
    ) -> list[MembershipRole]:
        now = datetime.now(UTC)
        query = (
            select(MembershipRole)
            .options(selectinload(MembershipRole.role))
            .where(
                MembershipRole.membership_id == membership_id,
                MembershipRole.is_deleted.is_(False),
                or_(
                    MembershipRole.expires_at.is_(None),
                    MembershipRole.expires_at > now,
                ),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_role_ids_for_membership(
        self, membership_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        now = datetime.now(UTC)
        query = select(MembershipRole.role_id).where(
            MembershipRole.membership_id == membership_id,
            MembershipRole.is_deleted.is_(False),
            or_(
                MembershipRole.expires_at.is_(None),
                MembershipRole.expires_at > now,
            ),
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_permissions_for_membership(
        self, membership_id: uuid.UUID,
    ) -> set[str]:
        role_ids = await self.get_role_ids_for_membership(membership_id)
        if not role_ids:
            return set()

        query = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id.in_(role_ids),
                Permission.is_deleted.is_(False),
            )
        )
        result = await self.session.execute(query)
        return set(result.scalars().all())

    async def has_permission(
        self, membership_id: uuid.UUID, permission_code: str,
    ) -> bool:
        perms = await self.get_all_permissions_for_membership(membership_id)
        return permission_code in perms

    async def has_any_permission(
        self, membership_id: uuid.UUID, permission_codes: list[str],
    ) -> bool:
        perms = await self.get_all_permissions_for_membership(membership_id)
        return bool(perms & set(permission_codes))

    async def has_all_permissions(
        self, membership_id: uuid.UUID, permission_codes: list[str],
    ) -> bool:
        perms = await self.get_all_permissions_for_membership(membership_id)
        return set(permission_codes).issubset(perms)

    async def get_memberships_with_permission(
        self, permission_code: str,
    ) -> list[uuid.UUID]:
        query = (
            select(MembershipRole.membership_id)
            .join(RolePermission, RolePermission.role_id == MembershipRole.role_id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(
                Permission.code == permission_code,
                Permission.is_deleted.is_(False),
                MembershipRole.is_deleted.is_(False),
                or_(
                    MembershipRole.expires_at.is_(None),
                    MembershipRole.expires_at > datetime.now(UTC),
                ),
            )
            .distinct()
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_membership(
        self, membership_id: uuid.UUID,
    ) -> list[MembershipRole]:
        query = (
            select(MembershipRole)
            .options(selectinload(MembershipRole.role))
            .where(
                MembershipRole.membership_id == membership_id,
                MembershipRole.is_deleted.is_(False),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

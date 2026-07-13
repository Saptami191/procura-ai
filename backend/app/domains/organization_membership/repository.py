from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.domains.organization_membership.enums import MembershipStatus
from app.domains.organization_membership.models import OrganizationMembership
from app.repositories.base import BaseRepository
from app.repositories.pagination import Page, Pagination


class OrganizationMembershipRepository(
    BaseRepository[OrganizationMembership, uuid.UUID]
):
    model = OrganizationMembership

    async def create_membership(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        invited_by_user_id: uuid.UUID | None = None,
        is_owner: bool = False,
    ) -> OrganizationMembership:
        now = datetime.now(UTC)
        membership = OrganizationMembership(
            organization_id=organization_id,
            user_id=user_id,
            membership_status=MembershipStatus.PENDING,
            invited_at=now,
            invited_by_user_id=invited_by_user_id,
            is_owner=is_owner,
        )
        self.session.add(membership)
        await self.session.flush()
        await self.session.refresh(membership)
        return membership

    async def get_by_organization_and_user(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        include_deleted: bool = False,
    ) -> OrganizationMembership | None:
        query = select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user_id,
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_organization_members(
        self,
        organization_id: uuid.UUID,
        *,
        status: MembershipStatus | None = None,
        pagination: Pagination | None = None,
    ) -> Page[OrganizationMembership]:
        query = select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.is_deleted.is_(False),
        )
        if status:
            query = query.where(OrganizationMembership.membership_status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(OrganizationMembership.created_at.desc())
        if pagination:
            query = pagination.apply(query)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        page = pagination.page if pagination else 1
        page_size = pagination.limit if pagination else max(total, 1) if total > 0 else 1

        return Page(items=items, total=total, page=page, page_size=page_size)

    async def get_user_organizations(
        self,
        user_id: uuid.UUID,
        *,
        status: MembershipStatus | None = None,
        pagination: Pagination | None = None,
    ) -> Page[OrganizationMembership]:
        query = (
            select(OrganizationMembership)
            .options(selectinload(OrganizationMembership.organization))
            .where(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.is_deleted.is_(False),
            )
        )
        if status:
            query = query.where(OrganizationMembership.membership_status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(OrganizationMembership.created_at.desc())
        if pagination:
            query = pagination.apply(query)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        page = pagination.page if pagination else 1
        page_size = pagination.limit if pagination else max(total, 1) if total > 0 else 1

        return Page(items=items, total=total, page=page, page_size=page_size)

    async def exists(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        include_deleted: bool = False,
    ) -> bool:
        query = select(OrganizationMembership.id).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user_id,
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        query = query.limit(1)
        result = await self.session.execute(query)
        return result.scalars().first() is not None

    async def exists_active(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        query = (
            select(OrganizationMembership.id)
            .where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.membership_status == MembershipStatus.ACTIVE,
                OrganizationMembership.is_deleted.is_(False),
            )
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalars().first() is not None

    async def set_status(
        self,
        membership_id: uuid.UUID,
        status: MembershipStatus,
    ) -> OrganizationMembership:
        membership = await self._get_or_raise(membership_id)
        membership.membership_status = status
        await self.session.flush()
        await self.session.refresh(membership)
        return membership

    async def activate(
        self,
        membership_id: uuid.UUID,
    ) -> OrganizationMembership:
        now = datetime.now(UTC)
        membership = await self._get_or_raise(membership_id)
        membership.membership_status = MembershipStatus.ACTIVE
        membership.joined_at = now
        membership.accepted_at = now
        await self.session.flush()
        await self.session.refresh(membership)
        return membership

    async def accept_invitation(
        self,
        membership_id: uuid.UUID,
    ) -> OrganizationMembership:
        return await self.activate(membership_id)

    async def transfer_ownership(
        self,
        from_membership_id: uuid.UUID,
        to_membership_id: uuid.UUID,
    ) -> tuple[OrganizationMembership, OrganizationMembership]:
        old_owner = await self._get_or_raise(from_membership_id)
        new_owner = await self._get_or_raise(to_membership_id)

        if old_owner.organization_id != new_owner.organization_id:
            raise ValueError("Cannot transfer ownership across organizations")

        old_owner.is_owner = False
        new_owner.is_owner = True

        await self.session.flush()
        await self.session.refresh(old_owner)
        await self.session.refresh(new_owner)
        return old_owner, new_owner

    async def set_default(
        self,
        membership_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> OrganizationMembership:
        query = (
            select(OrganizationMembership)
            .where(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.is_default.is_(True),
                OrganizationMembership.is_deleted.is_(False),
            )
        )
        result = await self.session.execute(query)
        current_default = result.scalars().first()

        if current_default and current_default.id != membership_id:
            current_default.is_default = False
            await self.session.flush()

        membership = await self._get_or_raise(membership_id)
        membership.is_default = True
        await self.session.flush()
        await self.session.refresh(membership)
        return membership

    async def get_owner(
        self,
        organization_id: uuid.UUID,
    ) -> OrganizationMembership | None:
        query = (
            select(OrganizationMembership)
            .where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.is_owner.is_(True),
                OrganizationMembership.is_deleted.is_(False),
                OrganizationMembership.membership_status == MembershipStatus.ACTIVE,
            )
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def count_active_members(
        self,
        organization_id: uuid.UUID,
    ) -> int:
        query = (
            select(func.count())
            .select_from(OrganizationMembership)
            .where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.membership_status == MembershipStatus.ACTIVE,
                OrganizationMembership.is_deleted.is_(False),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_default_for_user(
        self,
        user_id: uuid.UUID,
    ) -> OrganizationMembership | None:
        query = (
            select(OrganizationMembership)
            .options(selectinload(OrganizationMembership.organization))
            .where(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.is_default.is_(True),
                OrganizationMembership.is_deleted.is_(False),
            )
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def count_owners(
        self,
        organization_id: uuid.UUID,
    ) -> int:
        query = (
            select(func.count())
            .select_from(OrganizationMembership)
            .where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.is_owner.is_(True),
                OrganizationMembership.membership_status == MembershipStatus.ACTIVE,
                OrganizationMembership.is_deleted.is_(False),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def search_members(
        self,
        organization_id: uuid.UUID,
        query_str: str,
        *,
        pagination: Pagination | None = None,
    ) -> Page[OrganizationMembership]:
        pattern = f"%{query_str}%"
        filters = or_(
            OrganizationMembership.user_id.cast(str).ilike(pattern),
        )

        base_query = select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.is_deleted.is_(False),
            filters,
        )

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        query = base_query.order_by(OrganizationMembership.created_at.desc())
        if pagination:
            query = pagination.apply(query)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        page = pagination.page if pagination else 1
        page_size = pagination.limit if pagination else max(total, 1) if total > 0 else 1

        return Page(items=items, total=total, page=page, page_size=page_size)

    async def hard_delete_by_organization(self, organization_id: uuid.UUID) -> None:
        query = select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
        )
        result = await self.session.execute(query)
        memberships = list(result.scalars().all())
        for m in memberships:
            await self.session.delete(m)
        await self.session.flush()

    async def hard_delete_by_user(self, user_id: uuid.UUID) -> None:
        query = select(OrganizationMembership).where(
            OrganizationMembership.user_id == user_id,
        )
        result = await self.session.execute(query)
        memberships = list(result.scalars().all())
        for m in memberships:
            await self.session.delete(m)
        await self.session.flush()

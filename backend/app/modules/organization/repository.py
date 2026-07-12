from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select

from app.repositories.base import BaseRepository
from app.repositories.pagination import Page, Pagination
from app.repositories.sorting import SortDirection, Sorting

from .enums import OrganizationStatus
from .models import Organization


class OrganizationRepository(BaseRepository[Organization, uuid.UUID]):
    model = Organization

    async def get_by_slug(
        self,
        slug: str,
        *,
        include_deleted: bool = False,
    ) -> Organization | None:
        query = select(Organization).where(Organization.slug == slug)
        query = self._apply_soft_delete_filter(query, include_deleted)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def name_exists(self, name: str, *, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = select(Organization.id).where(
            func.lower(Organization.name) == func.lower(name),
            Organization.is_deleted.is_(False),
        )
        if exclude_id is not None:
            stmt = stmt.where(Organization.id != exclude_id)
        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    async def slug_exists(self, slug: str, *, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = select(Organization.id).where(
            Organization.slug == slug,
            Organization.is_deleted.is_(False),
        )
        if exclude_id is not None:
            stmt = stmt.where(Organization.id != exclude_id)
        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    async def list_active(
        self,
        *,
        pagination: Pagination | None = None,
    ) -> Page[Organization]:
        return await self.list(
            pagination=pagination,
            sortings=[Sorting(field="created_at", direction=SortDirection.DESC)],
        )

    async def search(
        self,
        query_str: str,
        *,
        pagination: Pagination | None = None,
    ) -> Page[Organization]:
        pattern = f"%{query_str}%"
        filters = or_(
            Organization.name.ilike(pattern),
            Organization.slug.ilike(pattern),
            Organization.description.ilike(pattern),
            Organization.industry.ilike(pattern),
        )
        # Use raw query with filter for search
        base_query = select(Organization).where(
            filters,
            Organization.is_deleted.is_(False),
        )

        # Count
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and sorting
        query = base_query.order_by(Organization.created_at.desc())
        if pagination:
            query = pagination.apply(query)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        page = pagination.page if pagination else 1
        page_size = pagination.limit if pagination else max(total, 1)

        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def count_by_status(self) -> dict[OrganizationStatus, int]:
        query = (
            select(Organization.status, func.count())
            .where(Organization.is_deleted.is_(False))
            .group_by(Organization.status)
        )
        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.fetchall()}

    async def set_active(self, organization_id: uuid.UUID, active: bool) -> None:
        org = await self._get_or_raise(organization_id)
        org.is_active = active
        await self.session.flush()
        await self.session.refresh(org)

    async def verify(self, organization_id: uuid.UUID) -> None:
        org = await self._get_or_raise(organization_id)
        org.is_verified = True
        await self.session.flush()
        await self.session.refresh(org)

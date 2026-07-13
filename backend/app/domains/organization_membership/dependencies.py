from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.domains.organization_membership.repository import (
    OrganizationMembershipRepository,
)
from app.domains.organization_membership.service import (
    OrganizationMembershipService,
)
from app.domains.user.repository import UserRepository
from app.modules.organization.repository import OrganizationRepository


async def get_membership_repository(
    session: AsyncSession = Depends(get_db),
) -> OrganizationMembershipRepository:
    return OrganizationMembershipRepository(session)


async def get_membership_service(
    membership_repo: OrganizationMembershipRepository = Depends(
        get_membership_repository,
    ),
    session: AsyncSession = Depends(get_db),
) -> OrganizationMembershipService:
    org_repo = OrganizationRepository(session)
    user_repo = UserRepository(session)
    return OrganizationMembershipService(membership_repo, org_repo, user_repo)

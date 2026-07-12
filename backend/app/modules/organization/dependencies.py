from __future__ import annotations

import uuid

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db

from .exceptions import OrganizationNotFoundError
from .models import Organization
from .repository import OrganizationRepository
from .service import OrganizationService


async def get_organization_repository(
    session: AsyncSession = Depends(get_db),
) -> OrganizationRepository:
    return OrganizationRepository(session)


async def get_organization_service(
    repository: OrganizationRepository = Depends(get_organization_repository),
) -> OrganizationService:
    return OrganizationService(repository)


async def get_organization_by_id(
    organization_id: uuid.UUID,
    service: OrganizationService = Depends(get_organization_service),
) -> Organization:
    org = await service.get_organization_model(organization_id)
    return org


async def get_organization_by_header(
    request: Request,
    x_organization_id: str | None = Header(None, alias="X-Organization-ID"),
    service: OrganizationService = Depends(get_organization_service),
) -> Organization | None:
    if x_organization_id is None:
        org_id = getattr(request.state, "organization_id", None)
        if org_id is None:
            return None
    else:
        try:
            org_id = uuid.UUID(x_organization_id)
        except ValueError:
            return None

    try:
        return await service.get_organization_model(org_id)
    except OrganizationNotFoundError:
        return None


async def get_current_organization(
    organization: Organization | None = Depends(get_organization_by_header),
) -> Organization:
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found. Provide X-Organization-ID header.",
        )
    if not organization.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is inactive",
        )
    return organization


async def organization_exists(
    organization_id: uuid.UUID,
    service: OrganizationService = Depends(get_organization_service),
) -> bool:
    return await service.organization_exists(organization_id)

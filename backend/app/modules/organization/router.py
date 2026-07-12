from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from .dependencies import (
    get_current_organization,
    get_organization_service,
)
from .models import Organization
from .schemas import (
    CreateOrganizationRequest,
    OrganizationListResponse,
    OrganizationResponse,
    UpdateOrganizationRequest,
)
from .service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
)
async def create_organization(
    data: CreateOrganizationRequest,
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationResponse:
    return await service.create_organization(data)


@router.get(
    "/",
    response_model=OrganizationListResponse,
    summary="List all organizations",
)
async def list_organizations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search query"),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationListResponse:
    if search:
        return await service.search_organizations(
            query=search, page=page, page_size=page_size,
        )
    return await service.list_organizations(page=page, page_size=page_size)


@router.get(
    "/by-slug/{slug}",
    response_model=OrganizationResponse,
    summary="Get organization by slug",
)
async def get_organization_by_slug(
    slug: str,
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationResponse:
    return await service.get_organization_by_slug(slug)


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get organization by ID",
)
async def get_organization(
    organization_id: uuid.UUID,
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationResponse:
    return await service.get_organization(organization_id)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
)
async def update_organization(
    organization_id: uuid.UUID,
    data: UpdateOrganizationRequest,
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationResponse:
    return await service.update_organization(organization_id, data)


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete organization",
)
async def delete_organization(
    organization_id: uuid.UUID,
    service: OrganizationService = Depends(get_organization_service),
) -> None:
    await service.delete_organization(organization_id)


@router.post(
    "/{organization_id}/restore",
    response_model=OrganizationResponse,
    summary="Restore soft-deleted organization",
)
async def restore_organization(
    organization_id: uuid.UUID,
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationResponse:
    return await service.restore_organization(organization_id)


@router.get(
    "/{organization_id}/check",
    summary="Check if organization exists and is active",
)
async def check_organization(
    organization_id: uuid.UUID,
    org: Organization = Depends(get_current_organization),
) -> dict:
    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "is_active": org.is_active,
        "status": org.status.value if org.status else None,
    }

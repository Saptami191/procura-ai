from __future__ import annotations

import uuid

from loguru import logger

from app.repositories.pagination import Pagination

from .exceptions import (
    OrganizationAlreadyExistsError,
    OrganizationInactiveError,
    OrganizationNotFoundError,
)
from .mapper import OrganizationMapper
from .models import Organization
from .repository import OrganizationRepository
from .schemas import (
    CreateOrganizationRequest,
    OrganizationListResponse,
    OrganizationResponse,
    UpdateOrganizationRequest,
)
from .validators import (
    generate_slug,
    validate_create_payload,
    validate_update_payload,
)


class OrganizationService:
    def __init__(self, repository: OrganizationRepository) -> None:
        self._repository = repository

    async def create_organization(
        self,
        data: CreateOrganizationRequest,
    ) -> OrganizationResponse:
        validated = validate_create_payload(data.model_dump())

        if await self._repository.name_exists(validated["name"]):
            raise OrganizationAlreadyExistsError(
                field="name", value=validated["name"],
            )

        slug = validated.get("slug") or generate_slug(validated["name"])
        if await self._repository.slug_exists(slug):
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
            validated["slug"] = slug
        else:
            validated["slug"] = slug

        org = await self._repository.create(validated)

        logger.info(
            "Organization created",
            organization_id=str(org.id),
            name=org.name,
            slug=org.slug,
        )

        return OrganizationMapper.to_response(org)

    async def get_organization(
        self,
        organization_id: uuid.UUID,
    ) -> OrganizationResponse:
        org = await self._repository.get_by_id(organization_id)
        if org is None:
            raise OrganizationNotFoundError(organization_id=str(organization_id))
        return OrganizationMapper.to_response(org)

    async def get_organization_by_slug(
        self,
        slug: str,
    ) -> OrganizationResponse:
        org = await self._repository.get_by_slug(slug)
        if org is None:
            raise OrganizationNotFoundError(slug=slug)
        return OrganizationMapper.to_response(org)

    async def update_organization(
        self,
        organization_id: uuid.UUID,
        data: UpdateOrganizationRequest,
    ) -> OrganizationResponse:
        org = await self._repository.get_by_id(organization_id)
        if org is None:
            raise OrganizationNotFoundError(organization_id=str(organization_id))

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return OrganizationMapper.to_response(org)

        validated = validate_update_payload(update_data)

        if "name" in validated:
            if await self._repository.name_exists(
                validated["name"], exclude_id=organization_id,
            ):
                raise OrganizationAlreadyExistsError(
                    field="name", value=validated["name"],
                )

        if "slug" in validated:
            if await self._repository.slug_exists(
                validated["slug"], exclude_id=organization_id,
            ):
                raise OrganizationAlreadyExistsError(
                    field="slug", value=validated["slug"],
                )

        updated = await self._repository.update(organization_id, validated)

        logger.info(
            "Organization updated",
            organization_id=str(organization_id),
            fields=list(validated.keys()),
        )

        return OrganizationMapper.to_response(updated)

    async def delete_organization(
        self,
        organization_id: uuid.UUID,
    ) -> None:
        org = await self._repository.get_by_id(organization_id)
        if org is None:
            raise OrganizationNotFoundError(organization_id=str(organization_id))

        await self._repository.delete(organization_id)

        logger.info(
            "Organization deleted (soft)",
            organization_id=str(organization_id),
        )

    async def restore_organization(
        self,
        organization_id: uuid.UUID,
    ) -> OrganizationResponse:
        org = await self._repository.restore(organization_id)
        logger.info(
            "Organization restored",
            organization_id=str(organization_id),
        )
        return OrganizationMapper.to_response(org)

    async def list_organizations(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> OrganizationListResponse:
        pagination = Pagination(page=page, limit=page_size)
        result = await self._repository.list(pagination=pagination)

        items = [OrganizationMapper.to_summary(o) for o in result.items]
        total_pages = max(1, (result.total + page_size - 1) // page_size)

        return OrganizationListResponse(
            items=items,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=total_pages,
        )

    async def search_organizations(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> OrganizationListResponse:
        pagination = Pagination(page=page, limit=page_size)
        result = await self._repository.search(query, pagination=pagination)

        items = [OrganizationMapper.to_summary(o) for o in result.items]
        total_pages = max(1, (result.total + page_size - 1) // page_size)

        return OrganizationListResponse(
            items=items,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=total_pages,
        )

    async def organization_exists(self, organization_id: uuid.UUID) -> bool:
        org = await self._repository.get_by_id(organization_id)
        return org is not None

    async def get_organization_model(
        self,
        organization_id: uuid.UUID,
    ) -> Organization:
        org = await self._repository.get_by_id(organization_id)
        if org is None:
            raise OrganizationNotFoundError(organization_id=str(organization_id))
        return org

    async def ensure_active(self, organization_id: uuid.UUID) -> Organization:
        org = await self.get_organization_model(organization_id)
        if not org.is_active:
            raise OrganizationInactiveError(
                organization_id=str(organization_id),
                status=org.status.value if org.status else "inactive",
            )
        return org

    async def _check_name_available(
        self,
        name: str,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        if await self._repository.name_exists(name, exclude_id=exclude_id):
            raise OrganizationAlreadyExistsError(field="name", value=name)

    async def _check_slug_available(
        self,
        slug: str,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        if await self._repository.slug_exists(slug, exclude_id=exclude_id):
            raise OrganizationAlreadyExistsError(field="slug", value=slug)

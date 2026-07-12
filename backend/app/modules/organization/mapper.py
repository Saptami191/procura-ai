from __future__ import annotations

from app.modules.organization.models import Organization
from app.modules.organization.schemas import (
    OrganizationResponse,
    OrganizationSummary,
)


class OrganizationMapper:
    @staticmethod
    def to_response(org: Organization) -> OrganizationResponse:
        return OrganizationResponse.model_validate(org)

    @staticmethod
    def to_summary(org: Organization) -> OrganizationSummary:
        return OrganizationSummary.model_validate(org)

    @staticmethod
    def to_response_list(orgs: list[Organization]) -> list[OrganizationResponse]:
        return [OrganizationMapper.to_response(o) for o in orgs]

    @staticmethod
    def to_summary_list(orgs: list[Organization]) -> list[OrganizationSummary]:
        return [OrganizationMapper.to_summary(o) for o in orgs]

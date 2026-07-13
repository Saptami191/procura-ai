from __future__ import annotations

from app.domains.organization_membership.models import OrganizationMembership
from app.domains.organization_membership.schemas import (
    MembershipResponse,
    MembershipSummary,
    UserOrganizationItem,
)


class MembershipMapper:
    @staticmethod
    def to_response(membership: OrganizationMembership) -> MembershipResponse:
        return MembershipResponse.model_validate(membership)

    @staticmethod
    def to_summary(membership: OrganizationMembership) -> MembershipSummary:
        return MembershipSummary.model_validate(membership)

    @staticmethod
    def to_user_org(membership: OrganizationMembership) -> UserOrganizationItem:
        org = membership.organization
        return UserOrganizationItem(
            id=membership.id,
            organization_id=membership.organization_id,
            organization_name=org.name if org else "",
            organization_slug=org.slug if org else "",
            membership_status=membership.membership_status,
            is_owner=membership.is_owner,
            is_default=membership.is_default,
            created_at=membership.created_at,
        )

    @staticmethod
    def to_response_list(memberships: list[OrganizationMembership]) -> list[MembershipResponse]:
        return [MembershipMapper.to_response(m) for m in memberships]

    @staticmethod
    def to_summary_list(memberships: list[OrganizationMembership]) -> list[MembershipSummary]:
        return [MembershipMapper.to_summary(m) for m in memberships]

    @staticmethod
    def to_user_org_list(memberships: list[OrganizationMembership]) -> list[UserOrganizationItem]:
        return [MembershipMapper.to_user_org(m) for m in memberships]

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.domains.organization_membership.dependencies import (
    get_membership_service,
)
from app.domains.organization_membership.enums import MembershipStatus
from app.domains.organization_membership.schemas import (
    AcceptInvitationRequest,
    InviteUserRequest,
    MembershipResponse,
    OrganizationMembersResponse,
    RejectInvitationRequest,
    UpdateMembershipRequest,
    UserOrganizationsResponse,
)
from app.domains.organization_membership.service import (
    OrganizationMembershipService,
)

router = APIRouter(prefix="", tags=["organization-memberships"])


@router.post(
    "/organizations/{organization_id}/members",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a user to join an organization",
)
async def invite_user(
    organization_id: uuid.UUID,
    data: InviteUserRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> MembershipResponse:
    return await service.invite_user(
        organization_id=organization_id,
        data=data,
        invited_by_user_id=current_user.id,
    )


@router.get(
    "/organizations/{organization_id}/members",
    response_model=OrganizationMembersResponse,
    summary="List all members of an organization",
)
async def list_organization_members(
    organization_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: MembershipStatus | None = Query(
        None, alias="status", description="Filter by membership status",
    ),
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> OrganizationMembersResponse:
    return await service.get_organization_members(
        organization_id=organization_id,
        page=page,
        page_size=page_size,
        status=status_filter,
    )


@router.get(
    "/users/{user_id}/organizations",
    response_model=UserOrganizationsResponse,
    summary="List all organizations a user belongs to",
)
async def list_user_organizations(
    user_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: MembershipStatus | None = Query(
        None, alias="status", description="Filter by membership status",
    ),
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> UserOrganizationsResponse:
    return await service.get_user_organizations(
        user_id=user_id,
        page=page,
        page_size=page_size,
        status=status_filter,
    )


@router.get(
    "/memberships/{membership_id}",
    response_model=MembershipResponse,
    summary="Get membership details",
)
async def get_membership(
    membership_id: uuid.UUID,
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> MembershipResponse:
    return await service.get_membership(membership_id)


@router.patch(
    "/memberships/{membership_id}",
    response_model=MembershipResponse,
    summary="Update membership (owner flags, default, metadata)",
)
async def update_membership(
    membership_id: uuid.UUID,
    data: UpdateMembershipRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> MembershipResponse:
    return await service.update_membership(membership_id, data)


@router.delete(
    "/memberships/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from an organization (admin action)",
)
async def remove_member(
    membership_id: uuid.UUID,
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> None:
    await service.remove_member(membership_id)


@router.post(
    "/memberships/{membership_id}/accept",
    response_model=MembershipResponse,
    summary="Accept an invitation to join an organization",
)
async def accept_invitation(
    membership_id: uuid.UUID,
    data: AcceptInvitationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> MembershipResponse:
    return await service.accept_invitation(membership_id, current_user.id)


@router.post(
    "/memberships/{membership_id}/reject",
    response_model=MembershipResponse,
    summary="Reject an invitation to join an organization",
)
async def reject_invitation(
    membership_id: uuid.UUID,
    data: RejectInvitationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> MembershipResponse:
    return await service.reject_invitation(membership_id, current_user.id)


@router.post(
    "/memberships/{membership_id}/activate",
    response_model=MembershipResponse,
    summary="Activate a pending or suspended membership",
)
async def activate_membership(
    membership_id: uuid.UUID,
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> MembershipResponse:
    return await service.activate_membership(membership_id)


@router.post(
    "/memberships/{membership_id}/suspend",
    response_model=MembershipResponse,
    summary="Suspend an active membership",
)
async def suspend_membership(
    membership_id: uuid.UUID,
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> MembershipResponse:
    return await service.suspend_membership(membership_id)


@router.post(
    "/memberships/{membership_id}/restore",
    response_model=MembershipResponse,
    summary="Restore a suspended membership to active",
)
async def restore_membership(
    membership_id: uuid.UUID,
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> MembershipResponse:
    return await service.restore_membership(membership_id)


@router.post(
    "/memberships/{membership_id}/default",
    response_model=MembershipResponse,
    summary="Set this membership as the user's default organization",
)
async def set_default_organization(
    membership_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> MembershipResponse:
    return await service.set_default_organization(membership_id, current_user.id)


@router.post(
    "/memberships/{membership_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave an organization (user-initiated)",
)
async def leave_organization(
    membership_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> None:
    await service.leave_organization(membership_id, current_user.id)


@router.post(
    "/organizations/{organization_id}/transfer-owner/{to_membership_id}",
    response_model=MembershipResponse,
    summary="Transfer organization ownership to another active member",
)
async def transfer_ownership(
    organization_id: uuid.UUID,
    to_membership_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: OrganizationMembershipService = Depends(get_membership_service),
) -> MembershipResponse:
    return await service.transfer_ownership(
        organization_id=organization_id,
        from_user_id=current_user.id,
        to_membership_id=to_membership_id,
    )

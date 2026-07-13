from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domains.organization_membership.enums import MembershipStatus


class InviteUserRequest(BaseModel):
    user_id: uuid.UUID
    is_owner: bool = False


class AcceptInvitationRequest(BaseModel):
    pass


class RejectInvitationRequest(BaseModel):
    reason: str | None = Field(None, max_length=500)


class UpdateMembershipRequest(BaseModel):
    is_owner: bool | None = None
    is_default: bool | None = None
    metadata: dict | None = None


class MembershipResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    membership_status: MembershipStatus
    joined_at: datetime | None
    invited_at: datetime | None
    accepted_at: datetime | None
    last_active_at: datetime | None
    invited_by_user_id: uuid.UUID | None
    is_owner: bool
    is_default: bool
    metadata: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MembershipSummary(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    membership_status: MembershipStatus
    is_owner: bool
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MembershipListResponse(BaseModel):
    items: list[MembershipSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class OrganizationMembersResponse(BaseModel):
    items: list[MembershipResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserOrganizationItem(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    organization_name: str
    organization_slug: str
    membership_status: MembershipStatus
    is_owner: bool
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserOrganizationsResponse(BaseModel):
    items: list[UserOrganizationItem]
    total: int
    page: int
    page_size: int
    total_pages: int

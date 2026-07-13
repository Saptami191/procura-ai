from __future__ import annotations

import uuid
from datetime import UTC, datetime

from loguru import logger

from app.domains.organization_membership.enums import MembershipStatus
from app.domains.organization_membership.exceptions import (
    CannotRemoveLastOwnerError,
    CannotRemoveOwnerError,
    DefaultOrganizationError,
    InvalidMembershipStateError,
    MembershipAlreadyExistsError,
    MembershipNotFoundError,
    OrganizationNotActiveError,
    UserNotActiveError,
)
from app.domains.organization_membership.mapper import MembershipMapper
from app.domains.organization_membership.repository import (
    OrganizationMembershipRepository,
)
from app.domains.organization_membership.schemas import (
    InviteUserRequest,
    MembershipResponse,
    OrganizationMembersResponse,
    UpdateMembershipRequest,
    UserOrganizationsResponse,
)
from app.domains.organization_membership.validators import (
    validate_invite_payload,
    validate_status_transition,
    validate_update_payload,
)
from app.domains.user.repository import UserRepository
from app.modules.organization.repository import OrganizationRepository
from app.repositories.pagination import Pagination


class OrganizationMembershipService:
    def __init__(
        self,
        membership_repo: OrganizationMembershipRepository,
        organization_repo: OrganizationRepository,
        user_repo: UserRepository,
    ) -> None:
        self._repo = membership_repo
        self._org_repo = organization_repo
        self._user_repo = user_repo

    async def invite_user(
        self,
        organization_id: uuid.UUID,
        data: InviteUserRequest,
        invited_by_user_id: uuid.UUID | None = None,
    ) -> MembershipResponse:
        validated = validate_invite_payload(data.model_dump())
        user_id = validated["user_id"]

        org = await self._org_repo.get_by_id(organization_id)
        if org is None:
            raise MembershipNotFoundError(organization_id=str(organization_id))
        if not org.is_active:
            raise OrganizationNotActiveError(organization_id=str(organization_id))

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise MembershipNotFoundError(user_id=str(user_id))
        if not user.is_active:
            raise UserNotActiveError(user_id=str(user_id))

        if await self._repo.exists(organization_id, user_id):
            raise MembershipAlreadyExistsError(
                organization_id=str(organization_id),
                user_id=str(user_id),
            )

        membership = await self._repo.create_membership(
            organization_id=organization_id,
            user_id=user_id,
            invited_by_user_id=invited_by_user_id,
            is_owner=validated.get("is_owner", False),
        )

        logger.info(
            "User invited to organization",
            user_id=str(user_id),
            organization_id=str(organization_id),
            membership_id=str(membership.id),
        )

        return MembershipMapper.to_response(membership)

    async def accept_invitation(
        self,
        membership_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> MembershipResponse:
        membership = await self._repo.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError(membership_id=str(membership_id))
        if membership.user_id != user_id:
            raise MembershipNotFoundError(membership_id=str(membership_id))

        validate_status_transition(
            membership.membership_status, MembershipStatus.ACTIVE,
        )

        org = await self._org_repo.get_by_id(membership.organization_id)
        if org is None or not org.is_active:
            raise OrganizationNotActiveError(
                organization_id=str(membership.organization_id),
            )

        updated = await self._repo.accept_invitation(membership_id)

        logger.info(
            "User accepted invitation",
            user_id=str(user_id),
            membership_id=str(membership_id),
            organization_id=str(membership.organization_id),
        )

        return MembershipMapper.to_response(updated)

    async def reject_invitation(
        self,
        membership_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> MembershipResponse:
        membership = await self._repo.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError(membership_id=str(membership_id))
        if membership.user_id != user_id:
            raise MembershipNotFoundError(membership_id=str(membership_id))

        validate_status_transition(
            membership.membership_status, MembershipStatus.REJECTED,
        )

        updated = await self._repo.set_status(membership_id, MembershipStatus.REJECTED)

        logger.info(
            "User rejected invitation",
            user_id=str(user_id),
            membership_id=str(membership_id),
        )

        return MembershipMapper.to_response(updated)

    async def get_membership(
        self,
        membership_id: uuid.UUID,
    ) -> MembershipResponse:
        membership = await self._repo.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError(membership_id=str(membership_id))
        return MembershipMapper.to_response(membership)

    async def update_membership(
        self,
        membership_id: uuid.UUID,
        data: UpdateMembershipRequest,
    ) -> MembershipResponse:
        membership = await self._repo.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError(membership_id=str(membership_id))

        update_data = validate_update_payload(data.model_dump(exclude_unset=True))
        if not update_data:
            return MembershipMapper.to_response(membership)

        if "is_default" in update_data and update_data["is_default"]:
            await self._repo.set_default(membership_id, membership.user_id)
            membership = await self._repo.get_by_id(membership_id)
            return MembershipMapper.to_response(membership)

        for key, value in update_data.items():
            if key == "metadata":
                setattr(membership, "metadata_", value)
            else:
                setattr(membership, key, value)

        await self._repo.session.flush()
        await self._repo.session.refresh(membership)

        logger.info(
            "Membership updated",
            membership_id=str(membership_id),
            fields=list(update_data.keys()),
        )

        return MembershipMapper.to_response(membership)

    async def remove_member(
        self,
        membership_id: uuid.UUID,
    ) -> None:
        membership = await self._repo.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError(membership_id=str(membership_id))

        if membership.is_owner:
            owner_count = await self._repo.count_owners(
                membership.organization_id,
            )
            if owner_count <= 1:
                raise CannotRemoveLastOwnerError(
                    organization_id=str(membership.organization_id),
                )
            raise CannotRemoveOwnerError(membership_id=str(membership_id))

        await self._repo.set_status(membership_id, MembershipStatus.REMOVED)
        await self._repo.soft_delete(membership_id)

        logger.info(
            "Member removed from organization",
            membership_id=str(membership_id),
            organization_id=str(membership.organization_id),
            user_id=str(membership.user_id),
        )

    async def activate_membership(
        self,
        membership_id: uuid.UUID,
    ) -> MembershipResponse:
        membership = await self._repo.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError(membership_id=str(membership_id))

        validate_status_transition(
            membership.membership_status, MembershipStatus.ACTIVE,
        )

        updated = await self._repo.activate(membership_id)

        logger.info(
            "Membership activated",
            membership_id=str(membership_id),
        )

        return MembershipMapper.to_response(updated)

    async def suspend_membership(
        self,
        membership_id: uuid.UUID,
    ) -> MembershipResponse:
        membership = await self._repo.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError(membership_id=str(membership_id))

        if membership.is_owner:
            raise CannotRemoveOwnerError(membership_id=str(membership_id))

        validate_status_transition(
            membership.membership_status, MembershipStatus.SUSPENDED,
        )

        updated = await self._repo.set_status(membership_id, MembershipStatus.SUSPENDED)

        logger.info(
            "Membership suspended",
            membership_id=str(membership_id),
        )

        return MembershipMapper.to_response(updated)

    async def restore_membership(
        self,
        membership_id: uuid.UUID,
    ) -> MembershipResponse:
        membership = await self._repo.get_by_id(membership_id, include_deleted=True)
        if membership is None:
            raise MembershipNotFoundError(membership_id=str(membership_id))

        if membership.is_deleted:
            await self._repo.restore(membership_id)

        validate_status_transition(
            membership.membership_status, MembershipStatus.ACTIVE,
        )

        updated = await self._repo.activate(membership_id)

        logger.info(
            "Membership restored",
            membership_id=str(membership_id),
        )

        return MembershipMapper.to_response(updated)

    async def set_default_organization(
        self,
        membership_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> MembershipResponse:
        membership = await self._repo.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError(membership_id=str(membership_id))
        if membership.user_id != user_id:
            raise MembershipNotFoundError(membership_id=str(membership_id))
        if membership.membership_status != MembershipStatus.ACTIVE:
            raise DefaultOrganizationError(
                message="Can only set active membership as default",
                details={
                    "membership_id": str(membership_id),
                    "current_status": membership.membership_status.value,
                },
            )

        updated = await self._repo.set_default(membership_id, user_id)

        logger.info(
            "Default organization set",
            user_id=str(user_id),
            organization_id=str(membership.organization_id),
        )

        return MembershipMapper.to_response(updated)

    async def leave_organization(
        self,
        membership_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        membership = await self._repo.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError(membership_id=str(membership_id))
        if membership.user_id != user_id:
            raise MembershipNotFoundError(membership_id=str(membership_id))

        if membership.is_owner:
            owner_count = await self._repo.count_owners(
                membership.organization_id,
            )
            if owner_count <= 1:
                raise CannotRemoveLastOwnerError(
                    organization_id=str(membership.organization_id),
                )
            raise CannotRemoveOwnerError(membership_id=str(membership_id))

        validate_status_transition(
            membership.membership_status, MembershipStatus.LEFT,
        )

        await self._repo.set_status(membership_id, MembershipStatus.LEFT)
        await self._repo.soft_delete(membership_id)

        logger.info(
            "User left organization",
            user_id=str(user_id),
            organization_id=str(membership.organization_id),
        )

    async def transfer_ownership(
        self,
        organization_id: uuid.UUID,
        from_user_id: uuid.UUID,
        to_membership_id: uuid.UUID,
    ) -> MembershipResponse:
        from_membership = await self._repo.get_by_organization_and_user(
            organization_id, from_user_id,
        )
        if from_membership is None:
            raise MembershipNotFoundError(
                organization_id=str(organization_id),
                user_id=str(from_user_id),
            )
        if not from_membership.is_owner:
            raise InvalidMembershipStateError(
                current_status=from_membership.membership_status.value,
                required_status="is_owner=True",
                action="transfer ownership",
            )

        to_membership = await self._repo.get_by_id(to_membership_id)
        if to_membership is None:
            raise MembershipNotFoundError(membership_id=str(to_membership_id))
        if to_membership.organization_id != organization_id:
            raise MembershipNotFoundError(membership_id=str(to_membership_id))
        if to_membership.membership_status != MembershipStatus.ACTIVE:
            raise InvalidMembershipStateError(
                current_status=to_membership.membership_status.value,
                required_status=MembershipStatus.ACTIVE.value,
                action="transfer ownership to this member",
            )

        _, new_owner = await self._repo.transfer_ownership(
            from_membership.id, to_membership_id,
        )

        logger.info(
            "Ownership transferred",
            organization_id=str(organization_id),
            from_user_id=str(from_user_id),
            to_user_id=str(to_membership.user_id),
        )

        return MembershipMapper.to_response(new_owner)

    async def get_organization_members(
        self,
        organization_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: MembershipStatus | None = None,
    ) -> OrganizationMembersResponse:
        pagination = Pagination(page=page, limit=page_size)
        result = await self._repo.get_organization_members(
            organization_id,
            status=status,
            pagination=pagination,
        )

        items = [MembershipMapper.to_response(m) for m in result.items]
        total_pages = max(1, (result.total + page_size - 1) // page_size)

        return OrganizationMembersResponse(
            items=items,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=total_pages,
        )

    async def get_user_organizations(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: MembershipStatus | None = None,
    ) -> UserOrganizationsResponse:
        pagination = Pagination(page=page, limit=page_size)
        result = await self._repo.get_user_organizations(
            user_id,
            status=status,
            pagination=pagination,
        )

        items = [MembershipMapper.to_user_org(m) for m in result.items]
        total_pages = max(1, (result.total + page_size - 1) // page_size)

        return UserOrganizationsResponse(
            items=items,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=total_pages,
        )

    async def update_last_active(
        self,
        membership_id: uuid.UUID,
    ) -> None:
        membership = await self._repo.get_by_id(membership_id)
        if membership is None:
            return
        membership.last_active_at = datetime.now(UTC)
        await self._repo.session.flush()

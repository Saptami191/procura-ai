from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domains.organization_membership.enums import MembershipStatus
from app.models.base import BaseModel


class OrganizationMembership(BaseModel):
    """
    Aggregate Root representing the relationship between an Organization and a User.

    Why this is NOT a join table:
    - Join tables (associative entities) exist only to resolve M:N relationships.
      They have no identity, no behavior, no lifecycle.
    - Membership has identity (UUID), lifecycle (PENDING→ACTIVE→SUSPENDED→LEFT),
      behavior (invite, accept, suspend, remove), and business rules.
    - Future RBAC, audit, notifications, billing all depend on Membership,
      not on the raw Org↔User pair.

    Why Aggregate Root:
    - Membership owns its children (future: role assignments, audit log entries).
    - External references always point to membership_id, never to (org_id, user_id).
    - Consistency boundaries: all membership operations go through the aggregate.
    """

    __tablename__ = "organization_memberships"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    membership_status: Mapped[MembershipStatus] = mapped_column(
        Enum(MembershipStatus, native_enum=False),
        default=MembershipStatus.PENDING,
        nullable=False,
    )

    joined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    invited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    invited_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_owner: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )

    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict,
    )

    # ORM relationships (informational, not used for queries)
    organization = relationship("Organization", foreign_keys=[organization_id])
    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])

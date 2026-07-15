from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domains.rbac.enums import PermissionCategory
from app.models.base import BaseModel


class Role(BaseModel):
    __tablename__ = "roles"
    """
    A named collection of permissions.

    Roles are the primary abstraction for grouping permissions.
    Users never get permissions directly — they get roles, and roles
    contain permissions.

    Why Organization ID is nullable:
      - System roles (Owner, Admin, Viewer) are defined once and shared
        across all organizations. No need to create N copies.
      - Organization-specific roles (custom roles) have an organization_id
        set and are scoped to that organization.
      - Null organization_id means "global system role". These cannot
        be deleted or modified by any organization admin.

    Why priority exists:
      - When a user holds multiple roles with conflicting permissions,
        the highest priority role's permissions win for "deny" decisions.
      - Future: priority-based resolution when ABAC rules conflict.
      - System roles have fixed priority (Owner=100, Admin=80, etc.).
    """

    __tablename__ = "roles"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(120), nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    is_system_role: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    priority: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict,
    )

    __table_args__ = (
        # Unique constraint: no two roles can have the same slug in the same scope
        # system_role slugs are unique globally; org role slugs are unique per org
    )

    # ORM relationships
    role_permissions = relationship(
        "RolePermission", back_populates="role", lazy="selectin",
    )
    membership_roles = relationship(
        "MembershipRole", back_populates="role", lazy="selectin",
    )


class Permission(BaseModel):
    """
    A single atomic action within the system.

    Permissions follow the resource.action naming convention:
      - purchase.create
      - supplier.read
      - invoice.approve
      - organization.manage

    Why Permission is an independent entity (not stored inside Role):
      - Permissions have identity and lifecycle independent of roles.
      - Multiple roles can reference the same permission — no duplication.
      - The full set of permissions in the system is discoverable:
        API consumers can list all available permissions.
      - Future ABAC policies reference permissions directly.
      - Future AI authorization references permission codes.
      - Deleting a permission from all roles is a single operation.

    Why resource.action naming:
      - Hierarchical: resource groups related actions.
      - Scannable: glob patterns work (purchase.* grants all purchase perms).
      - Predictable: developers know the convention without looking up docs.
      - Machine-parseable: the authorization engine can split on '.' for
        hierarchical resolution (future: grant "purchase.*").
    """

    __tablename__ = "permissions"

    resource: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False, index=True,
    )
    description: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
    )
    category: Mapped[PermissionCategory | None] = mapped_column(
        Enum(PermissionCategory, native_enum=False),
        nullable=True, index=True,
    )
    is_system_permission: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict,
    )

    # ORM relationships
    role_permissions = relationship(
        "RolePermission", back_populates="permission", lazy="selectin",
    )


class RolePermission(BaseModel):
    """
    Join entity linking Role and Permission.

    Why this table exists (not a many-to-many ORM relation):
      - Granular audit: who granted this permission to this role, and when.
      - Future: grant conditions (temporary permissions, scoped permissions).
      - Future: "inherited from" tracking for role hierarchy.
      - The granted_by/granted_at fields are essential for compliance audits.
    """

    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    # ORM relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")


class MembershipRole(BaseModel):
    """
    Links an OrganizationMembership to a Role.

    Why this is separate from OrganizationMembership:
      - A membership can hold MULTIPLE roles simultaneously.
      - Storing role_id on membership would limit it to exactly one role.
      - Multiple roles per member is essential: a user can be both
        "Procurement Manager" AND "Finance Approver" simultaneously.
      - Expiration support: roles can be time-bound (temp coverage,
        project-based authority delegation).
      - Audit trail: who assigned this role, when, and until when.

    Why not use the MembershipRole for Role→Permission directly:
      - MembershipRole connects a person to a role.
      - RolePermission connects a role to permissions.
      - This separation means changing a role's permissions automatically
        applies to everyone holding that role — no per-member updates.

    Support for role hierarchy (future):
      - A future "ParentRoleID" column on Role itself enables role
        inheritance (e.g., Admin inherits Viewer permissions).
      - MembershipRole remains unchanged — hierarchy is resolved at query time.
    """

    __tablename__ = "membership_roles"

    membership_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organization_memberships.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # ORM relationships
    role = relationship("Role", back_populates="membership_roles")

"""Create RBAC tables: roles, permissions, role_permissions, membership_roles

Revision ID: a4f8b2c3d5e6
Revises: c528ad29f94e
Create Date: 2026-07-15 22:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a4f8b2c3d5e6"
down_revision: Union[str, None] = "c528ad29f94e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── roles table ─────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_system_role", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("priority", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE",
        ),
    )
    op.create_index("ix_roles_organization_id", "roles", ["organization_id"])
    op.create_index("ix_roles_slug", "roles", ["slug"])
    op.create_unique_constraint(
        "uq_roles_slug_organization_id",
        "roles", ["slug", "organization_id"],
        postgresql_nulls_not_distinct=True,
    )

    # ── permissions table ───────────────────────────────────────
    op.create_table(
        "permissions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("resource", sa.String(50), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("code", sa.String(120), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("is_system_permission", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"], unique=True)
    op.create_index("ix_permissions_resource", "permissions", ["resource"])
    op.create_index("ix_permissions_category", "permissions", ["category"])
    op.create_unique_constraint(
        "uq_permissions_resource_action",
        "permissions", ["resource", "action"],
    )

    # ── role_permissions table ──────────────────────────────────
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("role_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("granted_by", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"])
    op.create_unique_constraint(
        "uq_role_permissions",
        "role_permissions", ["role_id", "permission_id"],
    )

    # ── membership_roles table ──────────────────────────────────
    op.create_table(
        "membership_roles",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("membership_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_by", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["membership_id"], ["organization_memberships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_membership_roles_membership_id", "membership_roles", ["membership_id"])
    op.create_index("ix_membership_roles_role_id", "membership_roles", ["role_id"])
    op.create_index("ix_membership_roles_membership_role", "membership_roles", ["membership_id", "role_id"])
    op.create_unique_constraint(
        "uq_membership_roles",
        "membership_roles", ["membership_id", "role_id"],
    )


def downgrade() -> None:
    op.drop_table("membership_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")

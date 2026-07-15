"""Create organization_memberships table

Revision ID: c528ad29f94e
Revises: 180ca54b7da0
Create Date: 2026-07-13 15:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c528ad29f94e'
down_revision: Union[str, None] = '180ca54b7da0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('organization_memberships',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False, index=True),
        sa.Column('user_id', sa.UUID(), nullable=False, index=True),
        sa.Column('membership_status', sa.String(length=50), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invited_by_user_id', sa.UUID(), nullable=True),
        sa.Column('is_owner', sa.Boolean(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_organization_memberships_organization_id_organizations'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_organization_memberships_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by_user_id'], ['users.id'], name=op.f('fk_organization_memberships_invited_by_user_id_users'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_organization_memberships')),
        sa.UniqueConstraint('organization_id', 'user_id', name=op.f('uq_organization_memberships_organization_id_user_id')),
    )
    op.create_index(
        op.f('ix_organization_memberships_membership_status'),
        'organization_memberships',
        ['membership_status'],
        unique=False,
    )
    op.create_index(
        op.f('ix_organization_memberships_is_owner'),
        'organization_memberships',
        ['is_owner'],
        unique=False,
    )
    op.create_index(
        op.f('ix_organization_memberships_is_default'),
        'organization_memberships',
        ['is_default'],
        unique=False,
    )
    op.create_index(
        op.f('ix_organization_memberships_organization_id_status'),
        'organization_memberships',
        ['organization_id', 'membership_status'],
        unique=False,
    )
    op.create_index(
        op.f('ix_organization_memberships_user_id_default'),
        'organization_memberships',
        ['user_id', 'is_default'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_organization_memberships_user_id_default'), table_name='organization_memberships')
    op.drop_index(op.f('ix_organization_memberships_organization_id_status'), table_name='organization_memberships')
    op.drop_index(op.f('ix_organization_memberships_is_default'), table_name='organization_memberships')
    op.drop_index(op.f('ix_organization_memberships_is_owner'), table_name='organization_memberships')
    op.drop_index(op.f('ix_organization_memberships_membership_status'), table_name='organization_memberships')
    op.drop_constraint(op.f('fk_organization_memberships_invited_by_user_id_users'), 'organization_memberships', type_='foreignkey')
    op.drop_constraint(op.f('fk_organization_memberships_user_id_users'), 'organization_memberships', type_='foreignkey')
    op.drop_constraint(op.f('fk_organization_memberships_organization_id_organizations'), 'organization_memberships', type_='foreignkey')
    op.drop_table('organization_memberships')

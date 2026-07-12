"""create_organizations_table

Revision ID: c12f8ec1cd9c
Revises: ea5fe3b440d4
Create Date: 2026-07-12 22:59:10.357411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c12f8ec1cd9c'
down_revision: Union[str, None] = 'ea5fe3b440d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('organizations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('company_size', sa.Integer(), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=True),
        sa.Column('timezone', sa.String(length=64), nullable=True),
        sa.Column('website', sa.String(length=2048), nullable=True),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='trial'),
        sa.Column('subscription_plan', sa.String(), nullable=False, server_default='free'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_organizations')),
        sa.UniqueConstraint('name', name=op.f('uq_organizations_name')),
        sa.UniqueConstraint('slug', name=op.f('uq_organizations_slug')),
    )
    op.create_index(op.f('ix_organizations_name'), 'organizations', ['name'], unique=True)
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)
    op.create_index(op.f('ix_organizations_status'), 'organizations', ['status'], unique=False)
    op.create_index(op.f('ix_organizations_subscription_plan'), 'organizations', ['subscription_plan'], unique=False)
    op.create_index(op.f('ix_organizations_is_active'), 'organizations', ['is_active'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_organizations_is_active'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_subscription_plan'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_status'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_name'), table_name='organizations')
    op.drop_table('organizations')

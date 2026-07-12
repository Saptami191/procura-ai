"""Rename and extend users table for domain-driven design

Revision ID: 180ca54b7da0
Revises: c12f8ec1cd9c
Create Date: 2026-07-13 01:14:56.338080

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '180ca54b7da0'
down_revision: Union[str, None] = 'c12f8ec1cd9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename columns (preserving existing data)
    op.alter_column('users', 'nickname', new_column_name='username')
    op.alter_column('users', 'avatar_url', new_column_name='profile_image_url')
    op.alter_column('users', 'profile_data', new_column_name='metadata')
    op.alter_column('users', 'is_verified', new_column_name='email_verified')

    # Drop organization_id (DDD separation - organizations are independent)
    op.drop_column('users', 'organization_id')

    # Add new columns
    op.add_column('users', sa.Column('display_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('job_title', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('department', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('preferred_language', sa.String(length=10), nullable=True))
    op.add_column('users', sa.Column('timezone', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('users', sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    # Rebuild constraints after renames
    op.drop_constraint(op.f('uq_users_nickname'), 'users', type_='unique')
    op.create_unique_constraint(op.f('uq_users_username'), 'users', ['username'])
    op.create_unique_constraint(op.f('uq_users_phone'), 'users', ['phone'])
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)


def downgrade() -> None:
    # Drop added indexes and constraints
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_is_active'), table_name='users')
    op.drop_constraint(op.f('uq_users_phone'), 'users', type_='unique')
    op.drop_constraint(op.f('uq_users_username'), 'users', type_='unique')

    # Restore old constraint
    op.create_unique_constraint(op.f('uq_users_nickname'), 'users', ['nickname'])

    # Drop added columns
    op.drop_column('users', 'phone_verified')
    op.drop_column('users', 'is_superuser')
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'preferred_language')
    op.drop_column('users', 'department')
    op.drop_column('users', 'job_title')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'display_name')

    # Restore organization_id
    op.add_column('users', sa.Column('organization_id', sa.UUID(), nullable=True))

    # Revert column renames (reverse order)
    op.alter_column('users', 'email_verified', new_column_name='is_verified')
    op.alter_column('users', 'metadata', new_column_name='profile_data')
    op.alter_column('users', 'profile_image_url', new_column_name='avatar_url')
    op.alter_column('users', 'username', new_column_name='nickname')

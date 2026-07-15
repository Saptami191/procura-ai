import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Register all models so Alembic detects them
from app.auth.models import LoginAttempt, RefreshToken, Session  # noqa: F401
from app.core import settings
from app.db.base import Base
from app.domains.organization_membership.models import OrganizationMembership  # noqa: F401
from app.domains.rbac.models import MembershipRole, Permission, Role, RolePermission  # noqa: F401
from app.domains.user.models import User  # noqa: F401
from app.modules.organization.models import Organization  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.database_url or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = settings.database_url or config.get_main_option("sqlalchemy.url")
    connectable = create_async_engine(url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

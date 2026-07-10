from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.types import CreateSchemaData, ModelT, UpdateSchemaData


async def get_or_create(
    session: AsyncSession,
    model: type[ModelT],
    defaults: dict[str, Any] | None = None,
    **filters: Any,
) -> tuple[ModelT, bool]:
    query = select(model).filter_by(**filters).limit(1)
    result = await session.execute(query)
    instance = result.scalars().first()

    if instance is not None:
        return instance, False

    data = {**filters, **(defaults or {})}
    instance = model(**data)
    session.add(instance)
    await session.flush()
    await session.refresh(instance)
    return instance, True


async def update_or_create(
    session: AsyncSession,
    model: type[ModelT],
    defaults: dict[str, Any],
    **filters: Any,
) -> tuple[ModelT, bool]:
    instance, created = await get_or_create(session, model, defaults=defaults, **filters)

    if not created:
        for key, value in defaults.items():
            setattr(instance, key, value)
        await session.flush()
        await session.refresh(instance)

    return instance, created


async def create_batch(
    session: AsyncSession,
    model: type[ModelT],
    items: list[CreateSchemaData],
) -> list[ModelT]:
    instances = [model(**data) for data in items]
    session.add_all(instances)
    await session.flush()
    for instance in instances:
        await session.refresh(instance)
    return instances


async def update_batch(
    session: AsyncSession,
    model: type[ModelT],
    ids: list[Any],
    data: UpdateSchemaData,
) -> int:
    from sqlalchemy import update as sa_update

    stmt = sa_update(model).where(model.id.in_(ids)).values(**data)
    result = await session.execute(stmt)
    await session.flush()
    return result.rowcount

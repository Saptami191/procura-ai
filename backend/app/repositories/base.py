from __future__ import annotations

from typing import Generic

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import Select

from app.repositories.exceptions import EntityNotFoundError
from app.repositories.filters import Filter
from app.repositories.pagination import Page, Pagination
from app.repositories.sorting import Sorting
from app.repositories.specifications import Specification
from app.repositories.types import (
    CreateSchemaData,
    ModelT,
    PKType,
    UpdateSchemaData,
)


class BaseRepository(Generic[ModelT, PKType]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: CreateSchemaData) -> ModelT:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(
        self,
        pk: PKType,
        *,
        include_deleted: bool = False,
    ) -> ModelT | None:
        query = select(self.model).where(self.model.id == pk)
        query = self._apply_soft_delete_filter(query, include_deleted)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get(
        self,
        *,
        filters: list[Filter] | None = None,
        specification: Specification | None = None,
        include_deleted: bool = False,
    ) -> ModelT | None:
        query = select(self.model)
        query = self._apply_soft_delete_filter(query, include_deleted)
        query = self._apply_filters(query, filters)
        query = self._apply_specification(query, specification)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list(
        self,
        *,
        pagination: Pagination | None = None,
        filters: list[Filter] | None = None,
        sortings: list[Sorting] | None = None,
        specification: Specification | None = None,
        include_deleted: bool = False,
    ) -> Page[ModelT]:
        query = select(self.model)
        query = self._apply_soft_delete_filter(query, include_deleted)
        query = self._apply_filters(query, filters)
        query = self._apply_specification(query, specification)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        query = self._apply_sorting(query, sortings)
        query = self._apply_pagination(query, pagination)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        page = pagination.page if pagination else 1
        page_size = pagination.limit if pagination else total if total > 0 else 1

        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update(
        self,
        pk: PKType,
        data: UpdateSchemaData,
    ) -> ModelT:
        instance = await self._get_or_raise(pk)
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(
        self,
        pk: PKType,
        *,
        hard: bool = False,
    ) -> None:
        if hard:
            instance = await self._get_or_raise(pk)
            await self.session.delete(instance)
            await self.session.flush()
            return

        await self.soft_delete(pk)

    async def exists(
        self,
        *,
        filters: list[Filter] | None = None,
        specification: Specification | None = None,
        include_deleted: bool = False,
    ) -> bool:
        query = select(self.model)
        query = self._apply_soft_delete_filter(query, include_deleted)
        query = self._apply_filters(query, filters)
        query = self._apply_specification(query, specification)
        query = query.limit(1)
        result = await self.session.execute(query)
        return result.scalars().first() is not None

    async def count(
        self,
        *,
        filters: list[Filter] | None = None,
        specification: Specification | None = None,
        include_deleted: bool = False,
    ) -> int:
        query = select(func.count()).select_from(self.model)
        query = self._apply_soft_delete_filter(query, include_deleted, bypass_from=True)
        query = self._apply_filters(query, filters)
        query = self._apply_specification(query, specification)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def bulk_create(self, items: list[CreateSchemaData]) -> list[ModelT]:
        instances = [self.model(**data) for data in items]
        self.session.add_all(instances)
        await self.session.flush()
        for instance in instances:
            await self.session.refresh(instance)
        return instances

    async def bulk_update(self, items: list[tuple[PKType, UpdateSchemaData]]) -> list[ModelT]:
        instances: list[ModelT] = []
        for pk, data in items:
            instance = await self._get_or_raise(pk)
            for key, value in data.items():
                setattr(instance, key, value)
            instances.append(instance)
        await self.session.flush()
        for instance in instances:
            await self.session.refresh(instance)
        return instances

    async def soft_delete(self, pk: PKType) -> ModelT:
        instance = await self._get_or_raise(pk)
        instance.is_deleted = True
        instance.deleted_at = func.now()
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def restore(self, pk: PKType) -> ModelT:
        query = select(self.model).where(
            self.model.id == pk,
            self.model.is_deleted == True,  # noqa: E712
        )
        result = await self.session.execute(query)
        instance = result.scalars().first()
        if instance is None:
            raise EntityNotFoundError(
                entity_name=self.model.__name__,
                entity_id=str(pk),
            )
        instance.is_deleted = False
        instance.deleted_at = None
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def _get_or_raise(self, pk: PKType) -> ModelT:
        instance = await self.get_by_id(pk, include_deleted=True)
        if instance is None:
            raise EntityNotFoundError(
                entity_name=self.model.__name__,
                entity_id=str(pk),
            )
        return instance

    def _apply_soft_delete_filter(
        self,
        query: Select,
        include_deleted: bool,
        bypass_from: bool = False,
    ) -> Select:
        if include_deleted:
            return query
        if not hasattr(self.model, "is_deleted"):
            return query
        column = self.model.is_deleted
        if bypass_from:
            return query.where(column == False)  # noqa: E712
        return query.where(column.is_(False))

    def _apply_filters(
        self,
        query: Select,
        filters: list[Filter] | None,
    ) -> Select:
        if not filters:
            return query
        for f in filters:
            query = f.apply(self.model, query)
        return query

    def _apply_sorting(
        self,
        query: Select,
        sortings: list[Sorting] | None,
    ) -> Select:
        if not sortings:
            return query.order_by(self.model.created_at.desc())
        for s in sortings:
            query = s.apply(self.model, query)
        return query

    def _apply_pagination(
        self,
        query: Select,
        pagination: Pagination | None,
    ) -> Select:
        if pagination is None:
            return query
        return pagination.apply(query)

    def _apply_specification(
        self,
        query: Select,
        specification: Specification | None,
    ) -> Select:
        if specification is None:
            return query
        return specification.apply(self.model, query)

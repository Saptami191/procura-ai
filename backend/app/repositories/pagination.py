from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic

from sqlalchemy.sql.expression import Select

from app.repositories.types import ModelT


@dataclass
class Pagination:
    limit: int = 20
    offset: int = 0

    def apply(self, query: Select) -> Select:
        return query.limit(self.limit).offset(self.offset)

    @property
    def page(self) -> int:
        if self.limit == 0:
            return 1
        return (self.offset // self.limit) + 1

    @classmethod
    def from_page(cls, page: int = 1, page_size: int = 20) -> Pagination:
        return cls(limit=page_size, offset=(page - 1) * page_size)


@dataclass
class Page(Generic[ModelT]):
    items: list[ModelT]
    total: int
    page: int
    page_size: int
    pages: int = field(init=False)

    def __post_init__(self) -> None:
        if self.page_size > 0:
            self.pages = max(1, (self.total + self.page_size - 1) // self.page_size)
        else:
            self.pages = 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from sqlalchemy.sql.expression import Select


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class Sorting:
    field: str
    direction: SortDirection = SortDirection.ASC

    def apply(self, model: type, query: Select) -> Select:
        column = getattr(model, self.field, None)
        if column is None:
            return query

        if self.direction == SortDirection.DESC:
            return query.order_by(column.desc())
        return query.order_by(column.asc())

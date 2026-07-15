from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from sqlalchemy import ColumnExpressionArgument, and_, or_
from sqlalchemy.sql.expression import Select


class FilterOperator(StrEnum):
    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    NOT_IN = "not_in"
    LIKE = "like"
    ILIKE = "ilike"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


@dataclass
class Filter:
    field: str
    operator: FilterOperator
    value: Any = None

    def apply(self, model: type, query: Select) -> Select:
        column = getattr(model, self.field, None)
        if column is None:
            return query

        clause = self._build_clause(column)
        if clause is not None:
            return query.where(clause)
        return query

    def _build_clause(self, column: Any) -> ColumnExpressionArgument | None:
        op = self.operator

        if op == FilterOperator.EQ:
            return column == self.value
        if op == FilterOperator.NEQ:
            return column != self.value
        if op == FilterOperator.IN:
            return column.in_(self.value) if self.value else None
        if op == FilterOperator.NOT_IN:
            return column.notin_(self.value) if self.value else None
        if op == FilterOperator.LIKE:
            return column.like(self.value)
        if op == FilterOperator.ILIKE:
            return column.ilike(self.value)
        if op == FilterOperator.GT:
            return column > self.value
        if op == FilterOperator.GTE:
            return column >= self.value
        if op == FilterOperator.LT:
            return column < self.value
        if op == FilterOperator.LTE:
            return column <= self.value
        if op == FilterOperator.BETWEEN:
            return column.between(*self.value) if isinstance(self.value, list | tuple) else None
        if op == FilterOperator.IS_NULL:
            return column.is_(None)
        if op == FilterOperator.IS_NOT_NULL:
            return column.isnot(None)

        return None


class FilterGroup:
    def __init__(self, *filters: Filter, operator: str = "and") -> None:
        self.filters = list(filters)
        self.operator = operator

    def apply(self, model: type, query: Select) -> Select:
        clauses = [f.apply(model, query) for f in self.filters]
        clauses = [c for c in clauses if c is not None]

        if not clauses:
            return query

        if self.operator == "or":
            return query.where(or_(*clauses))
        return query.where(and_(*clauses))

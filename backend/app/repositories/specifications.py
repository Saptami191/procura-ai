from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.sql.expression import Select


class Specification(ABC):
    @abstractmethod
    def apply(self, model: type, query: Select) -> Select:
        ...


class AndSpecification(Specification):
    def __init__(self, *specifications: Specification) -> None:
        self.specifications = list(specifications)

    def apply(self, model: type, query: Select) -> Select:
        for spec in self.specifications:
            query = spec.apply(model, query)
        return query


class OrSpecification(Specification):
    def __init__(self, *specifications: Specification) -> None:
        self.specifications = list(specifications)

    def apply(self, model: type, query: Select) -> Select:
        from sqlalchemy import or_

        sub_queries = []
        for spec in self.specifications:
            from copy import deepcopy

            sub_query = spec.apply(model, deepcopy(query))
            sub_queries.append(sub_query.whereclause)

        sub_queries = [q for q in sub_queries if q is not None]
        if sub_queries:
            return query.where(or_(*sub_queries))
        return query


class NotSpecification(Specification):
    def __init__(self, specification: Specification) -> None:
        self.specification = specification

    def apply(self, model: type, query: Select) -> Select:
        from sqlalchemy import not_

        sub_query = self.specification.apply(model, query)
        if sub_query.whereclause is not None:
            return query.where(not_(sub_query.whereclause))
        return query

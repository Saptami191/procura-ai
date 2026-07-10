from __future__ import annotations

from typing import Any

from app.core.exceptions import AppException


class RepositoryError(AppException):
    def __init__(
        self,
        message: str = "Repository operation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="REPOSITORY_ERROR",
            status_code=500,
            details=details,
        )


class EntityNotFoundError(RepositoryError):
    def __init__(
        self,
        entity_name: str = "Entity",
        entity_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged = {**(details or {}), "entity_name": entity_name}
        if entity_id is not None:
            merged["entity_id"] = entity_id
        super().__init__(
            message=f"{entity_name} not found",
            details=merged,
        )


class DuplicateEntityError(RepositoryError):
    def __init__(
        self,
        entity_name: str = "Entity",
        fields: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged = {**(details or {}), "entity_name": entity_name}
        if fields:
            merged["fields"] = fields
        super().__init__(
            message=f"{entity_name} already exists",
            details=merged,
        )


class TransactionError(RepositoryError):
    def __init__(
        self,
        message: str = "Transaction failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="TRANSACTION_ERROR",
            details=details,
        )

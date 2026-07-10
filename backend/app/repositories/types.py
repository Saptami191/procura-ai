from __future__ import annotations

import uuid
from typing import Any, TypeVar

from app.models.base import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)
PKType = TypeVar("PKType", uuid.UUID, int)

CreateSchemaData = dict[str, Any]
UpdateSchemaData = dict[str, Any]

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domains.rbac.enums import PermissionCategory, SystemRole

# ── Role Schemas ────────────────────────────────────────────────

class RoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = Field(None, max_length=500)
    priority: int = Field(0, ge=0, le=100)
    metadata: dict | None = None


class RoleUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    priority: int | None = Field(None, ge=0, le=100)
    metadata: dict | None = None


class RoleResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID | None
    name: str
    slug: str
    description: str | None
    is_system_role: bool
    priority: int
    metadata: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoleSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_system_role: bool
    priority: int

    model_config = {"from_attributes": True}


class PaginatedRoleResponse(BaseModel):
    items: list[RoleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Permission Schemas ──────────────────────────────────────────

class PermissionCreateRequest(BaseModel):
    resource: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")
    action: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")
    description: str | None = Field(None, max_length=255)
    category: PermissionCategory | None = None
    metadata: dict | None = None


class PermissionUpdateRequest(BaseModel):
    description: str | None = Field(None, max_length=255)
    category: PermissionCategory | None = None
    metadata: dict | None = None


class PermissionResponse(BaseModel):
    id: uuid.UUID
    resource: str
    action: str
    code: str
    description: str | None
    category: PermissionCategory | None
    is_system_permission: bool
    metadata: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PermissionSummary(BaseModel):
    id: uuid.UUID
    code: str
    resource: str
    action: str
    category: PermissionCategory | None

    model_config = {"from_attributes": True}


class PaginatedPermissionResponse(BaseModel):
    items: list[PermissionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Role-Permission Assignment ──────────────────────────────────

class AssignPermissionRequest(BaseModel):
    permission_ids: list[uuid.UUID] = Field(..., min_length=1)


class RolePermissionResponse(BaseModel):
    id: uuid.UUID
    role_id: uuid.UUID
    permission_id: uuid.UUID
    granted_by: uuid.UUID | None
    granted_at: datetime

    model_config = {"from_attributes": True}


# ── Membership-Role Assignment ──────────────────────────────────

class AssignRoleRequest(BaseModel):
    role_ids: list[uuid.UUID] = Field(..., min_length=1)
    expires_at: datetime | None = None


class MembershipRoleResponse(BaseModel):
    id: uuid.UUID
    membership_id: uuid.UUID
    role_id: uuid.UUID
    role_name: str = ""
    assigned_by: uuid.UUID | None
    assigned_at: datetime
    expires_at: datetime | None

    model_config = {"from_attributes": True}


# ── Authorization Check ─────────────────────────────────────────

class PermissionCheckRequest(BaseModel):
    permission_codes: list[str] = Field(..., min_length=1)


class PermissionCheckResponse(BaseModel):
    granted: bool
    missing_permissions: list[str] = []


class CurrentPermissionsResponse(BaseModel):
    membership_id: uuid.UUID
    role_ids: list[uuid.UUID]
    role_names: list[str]
    permission_codes: list[str]


# ── System Bootstrap ────────────────────────────────────────────

class SystemRoleDefinition(BaseModel):
    name: str
    slug: str
    description: str
    priority: int
    permission_codes: list[str]


class BootstrapRequest(BaseModel):
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role_slug: str = SystemRole.OWNER


class BootstrapResponse(BaseModel):
    role_id: uuid.UUID
    membership_role_id: uuid.UUID
    message: str

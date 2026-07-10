from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=255)
    nickname: str | None = Field(None, min_length=2, max_length=255)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    nickname: str | None = Field(None, min_length=2, max_length=255)
    is_active: bool | None = None
    avatar_url: str | None = None


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    nickname: str | None
    is_active: bool
    is_verified: bool
    profile_data: dict | None
    avatar_url: str | None
    last_login_at: datetime | None
    organization_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    nickname: str | None = Field(None, min_length=2, max_length=255)
    avatar_url: str | None = None

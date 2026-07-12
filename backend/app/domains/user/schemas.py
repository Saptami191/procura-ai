from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from .validators import (
    validate_country_code,
    validate_display_name,
    validate_phone,
    validate_timezone,
    validate_username,
)


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    username: str | None = Field(None, min_length=2, max_length=255)
    full_name: str | None = Field(None, max_length=255)
    display_name: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=20)
    job_title: str | None = Field(None, max_length=255)
    department: str | None = Field(None, max_length=255)
    preferred_language: str | None = Field(None, max_length=10)
    timezone: str | None = Field(None, max_length=64)

    @field_validator("username", mode="before")
    @classmethod
    def _validate_username(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_username(v)
        return v

    @field_validator("display_name", mode="before")
    @classmethod
    def _validate_display_name(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_display_name(v)
        return v

    @field_validator("phone", mode="before")
    @classmethod
    def _validate_phone(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_phone(v)
        return v

    @field_validator("preferred_language", mode="before")
    @classmethod
    def _validate_language(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_country_code(v)
        return v

    @field_validator("timezone", mode="before")
    @classmethod
    def _validate_timezone(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_timezone(v)
        return v


class UpdateUserRequest(BaseModel):
    username: str | None = Field(None, min_length=2, max_length=255)
    full_name: str | None = Field(None, max_length=255)
    display_name: str | None = Field(None, max_length=255)
    profile_image_url: str | None = None
    phone: str | None = Field(None, max_length=20)
    job_title: str | None = Field(None, max_length=255)
    department: str | None = Field(None, max_length=255)
    preferred_language: str | None = Field(None, max_length=10)
    timezone: str | None = Field(None, max_length=64)
    is_active: bool | None = None
    is_superuser: bool | None = None

    @field_validator("username", mode="before")
    @classmethod
    def _validate_username(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_username(v)
        return v

    @field_validator("display_name", mode="before")
    @classmethod
    def _validate_display_name(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_display_name(v)
        return v

    @field_validator("phone", mode="before")
    @classmethod
    def _validate_phone(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_phone(v)
        return v

    @field_validator("preferred_language", mode="before")
    @classmethod
    def _validate_language(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_country_code(v)
        return v

    @field_validator("timezone", mode="before")
    @classmethod
    def _validate_timezone(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_timezone(v)
        return v


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str | None
    full_name: str | None
    display_name: str | None
    profile_image_url: str | None
    phone: str | None
    job_title: str | None
    department: str | None
    preferred_language: str | None
    timezone: str | None
    is_active: bool
    is_superuser: bool
    email_verified: bool
    phone_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserSummary(BaseModel):
    id: uuid.UUID
    email: str
    username: str | None
    full_name: str | None
    display_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class CurrentUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str | None
    full_name: str | None
    display_name: str | None
    profile_image_url: str | None
    phone: str | None
    job_title: str | None
    department: str | None
    preferred_language: str | None
    timezone: str | None
    is_active: bool
    is_superuser: bool
    email_verified: bool
    phone_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

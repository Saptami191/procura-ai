from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .enums import OrganizationStatus, SubscriptionPlan
from .validators import (
    validate_country,
    validate_name,
    validate_slug,
    validate_timezone,
    validate_website,
)


class CreateOrganizationRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = Field(None)
    industry: str | None = Field(None, max_length=100)
    company_size: int | None = Field(None, ge=1, le=10_000_000)
    country: str | None = Field(None, pattern=r"^[A-Z]{2}$")
    timezone: str | None = Field(None)
    website: str | None = Field(None, max_length=2048)
    logo_url: str | None = Field(None)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        return validate_name(v)

    @field_validator("slug", mode="before")
    @classmethod
    def _validate_slug(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_slug(v)
        return v

    @field_validator("website", mode="before")
    @classmethod
    def _validate_website(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_website(v)
        return v

    @field_validator("country", mode="before")
    @classmethod
    def _validate_country(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_country(v)
        return v

    @field_validator("timezone", mode="before")
    @classmethod
    def _validate_timezone(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_timezone(v)
        return v


class UpdateOrganizationRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    slug: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = Field(None)
    industry: str | None = Field(None, max_length=100)
    company_size: int | None = Field(None, ge=1, le=10_000_000)
    country: str | None = Field(None, pattern=r"^[A-Z]{2}$")
    timezone: str | None = Field(None)
    website: str | None = Field(None, max_length=2048)
    logo_url: str | None = Field(None)
    status: str | None = Field(None)
    subscription_plan: str | None = Field(None)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_name(v)
        return v

    @field_validator("slug", mode="before")
    @classmethod
    def _validate_slug(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_slug(v)
        return v

    @field_validator("website", mode="before")
    @classmethod
    def _validate_website(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_website(v)
        return v

    @field_validator("country", mode="before")
    @classmethod
    def _validate_country(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_country(v)
        return v

    @field_validator("timezone", mode="before")
    @classmethod
    def _validate_timezone(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_timezone(v)
        return v


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    industry: str | None
    company_size: int | None
    country: str | None
    timezone: str | None
    website: str | None
    logo_url: str | None
    status: OrganizationStatus
    subscription_plan: SubscriptionPlan
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: OrganizationStatus
    subscription_plan: SubscriptionPlan
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class OrganizationListResponse(BaseModel):
    items: list[OrganizationSummary]
    total: int
    page: int
    page_size: int
    total_pages: int

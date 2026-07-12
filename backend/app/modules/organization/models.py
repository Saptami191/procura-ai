from __future__ import annotations

from sqlalchemy import Boolean, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

from .enums import OrganizationStatus, SubscriptionPlan


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    industry: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )
    company_size: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )
    country: Mapped[str | None] = mapped_column(
        String(2), nullable=True,
    )
    timezone: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
    )
    website: Mapped[str | None] = mapped_column(
        String(2048), nullable=True,
    )
    logo_url: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    status: Mapped[OrganizationStatus] = mapped_column(
        Enum(OrganizationStatus, native_enum=False),
        default=OrganizationStatus.TRIAL,
        nullable=False,
        index=True,
    )
    subscription_plan: Mapped[SubscriptionPlan] = mapped_column(
        Enum(SubscriptionPlan, native_enum=False),
        default=SubscriptionPlan.FREE,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict,
    )

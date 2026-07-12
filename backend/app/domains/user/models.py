from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )
    username: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True,
    )

    full_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
    )
    display_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
    )
    profile_image_url: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True,
    )
    job_title: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
    )
    department: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
    )
    preferred_language: Mapped[str | None] = mapped_column(
        String(10), nullable=True,
    )
    timezone: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True,
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    phone_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict,
    )

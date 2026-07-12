from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domains.user.schemas import (
    CreateUserRequest,
    CurrentUserResponse,
    UpdateUserRequest,
    UserListResponse,
    UserResponse,
    UserSummary,
)


class TestCreateUserRequest:
    def test_valid_request(self):
        data = CreateUserRequest(
            email="user@example.com",
            password="securePassword123!",
        )
        assert data.email == "user@example.com"
        assert data.username is None

    def test_with_all_fields(self):
        data = CreateUserRequest(
            email="user@example.com",
            password="securePassword123!",
            username="john_doe",
            full_name="John Doe",
            display_name="Johnny",
            phone="+1234567890",
            job_title="Engineer",
            department="Engineering",
            preferred_language="en",
            timezone="America/New_York",
        )
        assert data.username == "john_doe"

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            CreateUserRequest(email="user@example.com", password="short")

    def test_password_too_long(self):
        with pytest.raises(ValidationError):
            CreateUserRequest(email="user@example.com", password="a" * 129)

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            CreateUserRequest(email="not-an-email", password="validPass123!")

    def test_invalid_phone(self):
        with pytest.raises(ValidationError):
            CreateUserRequest(
                email="user@example.com",
                password="validPass123!",
                phone="abc",
            )

    def test_invalid_language(self):
        with pytest.raises(ValidationError):
            CreateUserRequest(
                email="user@example.com",
                password="validPass123!",
                preferred_language="english",
            )

    def test_invalid_timezone(self):
        with pytest.raises(ValidationError):
            CreateUserRequest(
                email="user@example.com",
                password="validPass123!",
                timezone="invalid",
            )


class TestUpdateUserRequest:
    def test_empty_update(self):
        data = UpdateUserRequest()
        assert data.model_dump(exclude_unset=True) == {}

    def test_partial_update(self):
        data = UpdateUserRequest(full_name="New Name", phone="+9876543210")
        dumped = data.model_dump(exclude_unset=True)
        assert dumped["full_name"] == "New Name"
        assert dumped["phone"] == "+9876543210"
        assert "username" not in dumped

    def test_boolean_fields(self):
        data = UpdateUserRequest(is_active=False, is_superuser=True)
        assert data.is_active is False
        assert data.is_superuser is True

    def test_invalid_phone_raises(self):
        with pytest.raises(ValidationError):
            UpdateUserRequest(phone="not-a-phone")


class TestUserResponse:
    def test_from_orm_like(self):
        now = datetime.now(UTC)
        data = UserResponse(
            id=uuid.uuid4(),
            email="user@example.com",
            username="john_doe",
            full_name="John Doe",
            display_name="Johnny",
            profile_image_url=None,
            phone="+1234567890",
            job_title="Engineer",
            department="Engineering",
            preferred_language="en",
            timezone="America/New_York",
            is_active=True,
            is_superuser=False,
            email_verified=True,
            phone_verified=False,
            last_login_at=now,
            created_at=now,
            updated_at=now,
        )
        assert data.email == "user@example.com"
        assert data.is_superuser is False

    def test_nullable_fields(self):
        now = datetime.now(UTC)
        data = UserResponse(
            id=uuid.uuid4(),
            email="user@example.com",
            username=None,
            full_name=None,
            display_name=None,
            profile_image_url=None,
            phone=None,
            job_title=None,
            department=None,
            preferred_language=None,
            timezone=None,
            is_active=True,
            is_superuser=False,
            email_verified=False,
            phone_verified=False,
            last_login_at=None,
            created_at=now,
            updated_at=now,
        )
        assert data.username is None
        assert data.last_login_at is None


class TestUserSummary:
    def test_minimal_fields(self):
        now = datetime.now(UTC)
        data = UserSummary(
            id=uuid.uuid4(),
            email="user@example.com",
            username="johnd",
            full_name="John Doe",
            display_name="Johnny",
            is_active=True,
            is_superuser=False,
            created_at=now,
        )
        assert data.id is not None


class TestUserListResponse:
    def test_pagination(self):
        now = datetime.now(UTC)
        item = UserSummary(
            id=uuid.uuid4(),
            email="user@example.com",
            username="johnd",
            full_name="John",
            display_name="John",
            is_active=True,
            is_superuser=False,
            created_at=now,
        )
        response = UserListResponse(
            items=[item, item],
            total=50,
            page=1,
            page_size=20,
            total_pages=3,
        )
        assert len(response.items) == 2
        assert response.total_pages == 3


class TestCurrentUserResponse:
    def test_full_profile(self):
        now = datetime.now(UTC)
        data = CurrentUserResponse(
            id=uuid.uuid4(),
            email="user@example.com",
            username="johnd",
            full_name="John Doe",
            display_name="Johnny",
            profile_image_url="https://example.com/avatar.jpg",
            phone="+1234567890",
            job_title="Engineer",
            department="Engineering",
            preferred_language="en",
            timezone="America/New_York",
            is_active=True,
            is_superuser=False,
            email_verified=True,
            phone_verified=False,
            last_login_at=now,
            created_at=now,
            updated_at=now,
        )
        assert data.profile_image_url == "https://example.com/avatar.jpg"

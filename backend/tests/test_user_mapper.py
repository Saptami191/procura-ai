from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.domains.user.mapper import UserMapper
from app.domains.user.models import User


def _make_user(**overrides) -> User:
    now = datetime.now(UTC)
    fields = {
        "id": uuid.uuid4(),
        "email": "user@example.com",
        "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$hashvalue",
        "username": "johndoe",
        "full_name": "John Doe",
        "display_name": "Johnny",
        "profile_image_url": None,
        "phone": "+1234567890",
        "job_title": "Engineer",
        "department": "Engineering",
        "preferred_language": "en",
        "timezone": "America/New_York",
        "is_active": True,
        "is_superuser": False,
        "email_verified": True,
        "phone_verified": False,
        "last_login_at": now,
        "metadata_": None,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
        "is_deleted": False,
    }
    fields.update(overrides)
    user = User(**fields)
    return user


class TestToResponse:
    def test_converts_all_fields(self):
        user = _make_user()
        response = UserMapper.to_response(user)
        assert response.email == "user@example.com"
        assert response.username == "johndoe"
        assert response.display_name == "Johnny"
        assert response.phone == "+1234567890"
        assert response.job_title == "Engineer"
        assert response.department == "Engineering"
        assert response.preferred_language == "en"
        assert response.timezone == "America/New_York"
        assert response.is_superuser is False
        assert response.email_verified is True
        assert response.phone_verified is False
        assert response.id == user.id

    def test_excludes_password_hash(self):
        user = _make_user()
        response = UserMapper.to_response(user)
        assert not hasattr(response, "password_hash")


class TestToSummary:
    def test_contains_only_summary_fields(self):
        user = _make_user()
        summary = UserMapper.to_summary(user)
        assert summary.email == "user@example.com"
        assert summary.display_name == "Johnny"
        assert summary.is_superuser is False
        assert not hasattr(summary, "password_hash")
        assert not hasattr(summary, "phone")

    def test_null_display_falls_back(self):
        user = _make_user(display_name=None)
        summary = UserMapper.to_summary(user)
        assert summary.display_name is None


class TestToCurrent:
    def test_contains_full_profile(self):
        user = _make_user(last_login_at=datetime.now(UTC))
        current = UserMapper.to_current(user)
        assert current.email == "user@example.com"
        assert current.profile_image_url is None
        assert current.last_login_at is not None


class TestToListMethods:
    def test_to_response_list(self):
        users = [_make_user(), _make_user(email="other@example.com")]
        responses = UserMapper.to_response_list(users)
        assert len(responses) == 2
        assert responses[0].email != responses[1].email

    def test_to_summary_list(self):
        users = [_make_user(), _make_user()]
        summaries = UserMapper.to_summary_list(users)
        assert len(summaries) == 2

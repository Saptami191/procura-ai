from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.user.exceptions import (
    DuplicateEmailError,
    DuplicatePhoneError,
    DuplicateUsernameError,
    InactiveUserError,
    UserNotFoundError,
)
from app.domains.user.schemas import CreateUserRequest, UpdateUserRequest
from app.domains.user.service import UserService


def _make_user(**kwargs) -> MagicMock:
    fields = dict(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$hash",
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
        metadata_=None,
        created_at=MagicMock(),
        updated_at=MagicMock(),
    )
    fields.update(kwargs)
    return MagicMock(**fields)


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.session = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.get_by_username = AsyncMock()
    repo.get_by_phone = AsyncMock()
    repo.email_exists = AsyncMock(return_value=False)
    repo.username_exists = AsyncMock(return_value=False)
    repo.phone_exists = AsyncMock(return_value=False)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.list = AsyncMock()
    return repo


@pytest.fixture
def service(mock_repo):
    return UserService(mock_repo)


class TestCreateUser:
    async def test_creates_user_successfully(self, service, mock_repo):
        user = _make_user(
            email="test@example.com", username="testuser",
            full_name="Test User", display_name="Test User",
        )
        mock_repo.create.return_value = user
        data = CreateUserRequest(
            email="test@example.com",
            password="validPass123!",
            username="testuser",
        )
        result = await service.create_user(data)
        assert result.email == "test@example.com"

    async def test_raises_on_duplicate_email(self, service, mock_repo):
        mock_repo.email_exists.return_value = True
        data = CreateUserRequest(
            email="existing@example.com",
            password="validPass123!",
        )
        with pytest.raises(DuplicateEmailError):
            await service.create_user(data)

    async def test_raises_on_duplicate_username(self, service, mock_repo):
        mock_repo.username_exists.return_value = True
        data = CreateUserRequest(
            email="test@example.com",
            password="validPass123!",
            username="taken",
        )
        with pytest.raises(DuplicateUsernameError):
            await service.create_user(data)

    async def test_raises_on_duplicate_phone(self, service, mock_repo):
        mock_repo.phone_exists.return_value = True
        data = CreateUserRequest(
            email="test@example.com",
            password="validPass123!",
            phone="+1234567890",
        )
        with pytest.raises(DuplicatePhoneError):
            await service.create_user(data)

    async def test_creates_without_optional_fields(self, service, mock_repo):
        mock_repo.create.return_value = _make_user(email="minimal@example.com")
        data = CreateUserRequest(
            email="minimal@example.com",
            password="validPass123!",
        )
        result = await service.create_user(data)
        assert result.email == "minimal@example.com"


class TestGetUser:
    async def test_returns_user(self, service, mock_repo):
        user_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = _make_user(id=user_id, email="user@example.com")
        result = await service.get_user(user_id)
        assert result.email == "user@example.com"

    async def test_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(UserNotFoundError):
            await service.get_user(uuid.uuid4())


class TestGetUserSummary:
    async def test_returns_summary(self, service, mock_repo):
        user_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = _make_user(id=user_id, email="user@example.com")
        result = await service.get_user_summary(user_id)
        assert result.email == "user@example.com"

    async def test_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(UserNotFoundError):
            await service.get_user_summary(uuid.uuid4())


class TestUpdateUser:
    async def test_updates_full_name(self, service, mock_repo):
        user_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = _make_user(id=user_id, email="user@example.com")
        mock_repo.update.return_value = _make_user(
            id=user_id, email="user@example.com", full_name="New Name",
        )
        data = UpdateUserRequest(full_name="New Name")
        result = await service.update_user(user_id, data)
        assert result.email == "user@example.com"

    async def test_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(UserNotFoundError):
            await service.update_user(uuid.uuid4(), UpdateUserRequest())

    async def test_noop_when_empty_payload(self, service, mock_repo):
        user_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = _make_user(id=user_id, email="user@example.com")
        data = UpdateUserRequest()
        result = await service.update_user(user_id, data)
        assert result.email == "user@example.com"
        mock_repo.update.assert_not_called()

    async def test_checks_username_duplicate(self, service, mock_repo):
        user_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = _make_user(id=user_id)
        mock_repo.get_by_username.return_value = _make_user(id=uuid.uuid4())
        data = UpdateUserRequest(username="taken")
        with pytest.raises(DuplicateUsernameError):
            await service.update_user(user_id, data)

    async def test_allows_same_username(self, service, mock_repo):
        user_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = _make_user(id=user_id, email="user@example.com")
        mock_repo.get_by_username.return_value = _make_user(id=user_id)
        mock_repo.update.return_value = _make_user(
            id=user_id, email="user@example.com", username="myuser",
        )
        data = UpdateUserRequest(username="myuser")
        result = await service.update_user(user_id, data)
        assert result.email == "user@example.com"


class TestDeleteUser:
    async def test_deletes_user(self, service, mock_repo):
        user_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = _make_user(id=user_id)
        await service.delete_user(user_id)
        mock_repo.delete.assert_awaited_once_with(user_id)

    async def test_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(UserNotFoundError):
            await service.delete_user(uuid.uuid4())


class TestListUsers:
    async def test_returns_paginated(self, service, mock_repo):
        mock_repo.list.return_value = MagicMock(
            items=[_make_user(email="a@example.com"), _make_user(email="b@example.com")],
            total=2,
        )
        users, total = await service.list_users(skip=0, limit=20)
        assert len(users) == 2
        assert total == 2


class TestGetByEmail:
    async def test_returns_user(self, service, mock_repo):
        mock_repo.get_by_email.return_value = _make_user(email="test@example.com")
        result = await service.get_by_email("test@example.com")
        assert result is not None
        assert result.email == "test@example.com"

    async def test_returns_none(self, service, mock_repo):
        mock_repo.get_by_email.return_value = None
        result = await service.get_by_email("missing@example.com")
        assert result is None


class TestVerifyCredentials:
    async def test_valid_credentials(self, service, mock_repo):
        user = _make_user(password_hash="hash", is_active=True)
        mock_repo.get_by_email.return_value = user
        with patch("app.domains.user.service.verify_password", return_value=True):
            result = await service.verify_credentials("test@example.com", "pass")
        assert result is user

    async def test_wrong_password(self, service, mock_repo):
        mock_repo.get_by_email.return_value = _make_user(password_hash="hash", is_active=True)
        with patch("app.domains.user.service.verify_password", return_value=False):
            result = await service.verify_credentials("test@example.com", "wrong")
        assert result is None

    async def test_inactive_user(self, service, mock_repo):
        mock_repo.get_by_email.return_value = _make_user(password_hash="hash", is_active=False)
        with patch("app.domains.user.service.verify_password", return_value=True):
            result = await service.verify_credentials("test@example.com", "pass")
        assert result is None

    async def test_unknown_email(self, service, mock_repo):
        mock_repo.get_by_email.return_value = None
        result = await service.verify_credentials("unknown@example.com", "pass")
        assert result is None


class TestEnsureUserExists:
    async def test_active_user(self, service, mock_repo):
        user_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = _make_user(id=user_id, is_active=True)
        result = await service.ensure_user_exists(user_id)
        assert result.id == user_id

    async def test_inactive_user(self, service, mock_repo):
        mock_repo.get_by_id.return_value = _make_user(is_active=False)
        with pytest.raises(InactiveUserError):
            await service.ensure_user_exists(uuid.uuid4())

    async def test_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(UserNotFoundError):
            await service.ensure_user_exists(uuid.uuid4())

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.user.repository import UserRepository


@pytest.fixture
def repo():
    session = AsyncMock()
    execute_result = MagicMock()
    scalars_result = MagicMock()
    execute_result.scalars = MagicMock(return_value=scalars_result)
    session.execute = AsyncMock(return_value=execute_result)
    return UserRepository(session)


class TestGetByEmail:
    async def test_found(self, repo):
        expected_user = MagicMock()
        repo.session.execute.return_value.scalars.return_value.first.return_value = expected_user
        result = await repo.get_by_email("user@example.com")
        assert result is expected_user

    async def test_not_found(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = None
        result = await repo.get_by_email("missing@example.com")
        assert result is None


class TestGetByUsername:
    async def test_found(self, repo):
        expected = MagicMock()
        repo.session.execute.return_value.scalars.return_value.first.return_value = expected
        result = await repo.get_by_username("johndoe")
        assert result is expected

    async def test_not_found(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = None
        result = await repo.get_by_username("nobody")
        assert result is None


class TestGetByPhone:
    async def test_found(self, repo):
        expected = MagicMock()
        repo.session.execute.return_value.scalars.return_value.first.return_value = expected
        result = await repo.get_by_phone("+1234567890")
        assert result is expected

    async def test_not_found(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = None
        result = await repo.get_by_phone("+0000000000")
        assert result is None


class TestEmailExists:
    async def test_exists(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = uuid.uuid4()
        assert await repo.email_exists("user@example.com") is True

    async def test_not_exists(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = None
        assert await repo.email_exists("missing@example.com") is False


class TestUsernameExists:
    async def test_exists(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = uuid.uuid4()
        assert await repo.username_exists("johndoe") is True

    async def test_not_exists(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = None
        assert await repo.username_exists("nobody") is False


class TestPhoneExists:
    async def test_exists(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = uuid.uuid4()
        assert await repo.phone_exists("+1234567890") is True

    async def test_not_exists(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = None
        assert await repo.phone_exists("+0000000000") is False


class TestFindByEmailOrUsername:
    async def test_by_email(self, repo):
        expected = MagicMock()
        repo.session.execute.return_value.scalars.return_value.first.return_value = expected
        result = await repo.find_by_email_or_username("user@example.com")
        assert result is expected

    async def test_by_username(self, repo):
        expected = MagicMock()
        repo.session.execute.return_value.scalars.return_value.first.return_value = expected
        result = await repo.find_by_email_or_username("johndoe")
        assert result is expected

    async def test_not_found(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = None
        result = await repo.find_by_email_or_username("nobody")
        assert result is None

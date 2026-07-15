from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.rbac.repository import (
    MembershipRoleRepository,
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
)


@pytest.fixture
def session():
    s = AsyncMock()
    execute_result = MagicMock()
    scalars_result = MagicMock()
    execute_result.scalars = MagicMock(return_value=scalars_result)
    execute_result.scalar_one = MagicMock(return_value=0)
    s.execute = AsyncMock(return_value=execute_result)
    return s


class TestRoleRepository:
    @pytest.fixture
    def repo(self, session):
        return RoleRepository(session)

    async def test_find_by_slug_found(self, repo):
        expected = MagicMock()
        repo.session.execute.return_value.scalars.return_value.first.return_value = expected
        result = await repo.find_by_slug("admin")
        assert result is expected

    async def test_find_by_slug_not_found(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = None
        result = await repo.find_by_slug("nonexistent")
        assert result is None

    async def test_find_by_name_found(self, repo):
        expected = MagicMock()
        repo.session.execute.return_value.scalars.return_value.first.return_value = expected
        result = await repo.find_by_name("Admin")
        assert result is expected

    async def test_get_system_roles(self, repo):
        repo.session.execute.return_value.scalars.return_value.all.return_value = []
        result = await repo.get_system_roles()
        assert result == []

    async def test_get_org_roles(self, repo):
        repo.session.execute.return_value.scalars.return_value.all.return_value = []
        result = await repo.get_org_roles(uuid.uuid4())
        assert result == []


class TestPermissionRepository:
    @pytest.fixture
    def repo(self, session):
        return PermissionRepository(session)

    async def test_find_by_code_found(self, repo):
        expected = MagicMock()
        repo.session.execute.return_value.scalars.return_value.first.return_value = expected
        result = await repo.find_by_code("purchase.create")
        assert result is expected

    async def test_find_by_code_not_found(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = None
        result = await repo.find_by_code("nonexistent")
        assert result is None

    async def test_find_by_codes(self, repo):
        repo.session.execute.return_value.scalars.return_value.all.return_value = []
        result = await repo.find_by_codes(["a.b", "c.d"])
        assert result == []

    async def test_list_by_resource(self, repo):
        repo.session.execute.return_value.scalars.return_value.all.return_value = []
        result = await repo.list_by_resource("purchase")
        assert result == []

    async def test_search(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = 0
        repo.session.execute.return_value.scalars.return_value.all.return_value = []
        result = await repo.search("purchase")
        assert result.items == []


class TestRolePermissionRepository:
    @pytest.fixture
    def repo(self, session):
        return RolePermissionRepository(session)

    async def test_assign(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = None
        repo.session.add = MagicMock()
        repo.session.flush = AsyncMock()
        repo.session.refresh = AsyncMock()
        result = await repo.assign(uuid.uuid4(), uuid.uuid4())
        assert result is not None
        repo.session.add.assert_called_once()

    async def test_assign_existing(self, repo):
        existing = MagicMock()
        repo.session.execute.return_value.scalars.return_value.first.return_value = existing
        result = await repo.assign(uuid.uuid4(), uuid.uuid4())
        assert result is existing
        repo.session.add.assert_not_called()

    async def test_remove(self, repo):
        rp = MagicMock()
        repo.session.execute.return_value.scalars.return_value.first.return_value = rp
        await repo.remove(uuid.uuid4(), uuid.uuid4())
        repo.session.delete.assert_called_once_with(rp)

    async def test_remove_not_found(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = None
        await repo.remove(uuid.uuid4(), uuid.uuid4())
        repo.session.delete.assert_not_called()

    async def test_has_permission_true(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = uuid.uuid4()
        result = await repo.has_permission(uuid.uuid4(), "purchase.read")
        assert result is True

    async def test_has_permission_false(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = None
        result = await repo.has_permission(uuid.uuid4(), "purchase.read")
        assert result is False


class TestMembershipRoleRepository:
    @pytest.fixture
    def repo(self, session):
        return MembershipRoleRepository(session)

    async def test_assign(self, repo):
        repo.session.execute.return_value.scalars.return_value.first.return_value = None
        repo.session.add = MagicMock()
        repo.session.flush = AsyncMock()
        repo.session.refresh = AsyncMock()
        result = await repo.assign(uuid.uuid4(), uuid.uuid4(), expires_at=datetime.now(UTC))
        assert result is not None
        repo.session.add.assert_called_once()

    async def test_assign_existing(self, repo):
        existing = MagicMock()
        repo.session.execute.return_value.scalars.return_value.first.return_value = existing
        result = await repo.assign(uuid.uuid4(), uuid.uuid4())
        assert result is existing

    async def test_has_permission_true(self, repo):
        perms = MagicMock()
        perms.__contains__ = MagicMock(return_value=True)
        repo.session.execute.return_value.scalars.return_value.all.return_value = []
        result = await repo.has_permission(uuid.uuid4(), "purchase.read")
        assert result is False

    async def test_get_role_ids_returns_list(self, repo):
        repo.session.execute.return_value.scalars.return_value.all.return_value = []
        result = await repo.get_role_ids_for_membership(uuid.uuid4())
        assert result == []

    async def test_list_by_membership(self, repo):
        repo.session.execute.return_value.scalars.return_value.all.return_value = []
        result = await repo.list_by_membership(uuid.uuid4())
        assert result == []

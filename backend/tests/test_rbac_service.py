from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.rbac.exceptions import (
    DuplicatePermissionError,
    DuplicateRoleError,
    SystemRoleModificationError,
)
from app.domains.rbac.schemas import (
    AssignPermissionRequest,
    AssignRoleRequest,
    PermissionCreateRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
)
from app.domains.rbac.service import AuthorizationService

pytestmark = pytest.mark.filterwarnings(
    "ignore:coroutine.*AsyncMockMixin.*was never awaited:RuntimeWarning",
)


def _configure_session_for_create(session):
    """Configure a mock session to populate model objects on flush/refresh."""
    _added = []
    session.add.side_effect = lambda obj: _added.append(obj)

    async def _flush():
        now = datetime.now(UTC)
        for obj in _added:
            if obj.id is None:
                obj.id = uuid.uuid4()
            if obj.created_at is None:
                obj.created_at = now
            if obj.updated_at is None:
                obj.updated_at = now

    async def _refresh(obj):
        now = datetime.now(UTC)
        if obj.id is None:
            obj.id = uuid.uuid4()
        if obj.created_at is None:
            obj.created_at = now
        if obj.updated_at is None:
            obj.updated_at = now

    session.flush.side_effect = _flush
    session.refresh.side_effect = _refresh


def _make_role(**kwargs) -> MagicMock:
    role = MagicMock()
    role.id = uuid.uuid4()
    role.organization_id = None
    role.name = "Test Role"
    role.slug = "test_role"
    role.description = None
    role.is_system_role = False
    role.priority = 0
    role.metadata_ = None
    role.created_at = datetime.now(UTC)
    role.updated_at = datetime.now(UTC)
    for k, v in kwargs.items():
        setattr(role, k, v)
    return role


def _make_permission(**kwargs) -> MagicMock:
    perm = MagicMock()
    perm.id = uuid.uuid4()
    perm.resource = "purchase"
    perm.action = "create"
    perm.code = "purchase.create"
    perm.description = None
    perm.category = None
    perm.is_system_permission = False
    perm.metadata_ = None
    perm.created_at = datetime.now(UTC)
    perm.updated_at = datetime.now(UTC)
    for k, v in kwargs.items():
        setattr(perm, k, v)
    return perm


def _make_membership_role(role: MagicMock | None = None, **kwargs) -> MagicMock:
    if role is None:
        role = _make_role()
    mr = MagicMock()
    mr.id = uuid.uuid4()
    mr.membership_id = uuid.uuid4()
    mr.role_id = role.id
    mr.role = role
    mr.role_name = ""
    mr.assigned_by = None
    mr.assigned_at = datetime.now(UTC)
    mr.expires_at = None
    for k, v in kwargs.items():
        setattr(mr, k, v)
    return mr


@pytest.fixture
def repos():
    return {
        "role": AsyncMock(),
        "perm": AsyncMock(),
        "rp": AsyncMock(),
        "mr": AsyncMock(),
    }


@pytest.fixture
def service(repos):
    for r in repos.values():
        r.session = AsyncMock()
    return AuthorizationService(
        role_repo=repos["role"],
        permission_repo=repos["perm"],
        role_permission_repo=repos["rp"],
        membership_role_repo=repos["mr"],
    )


class TestCreateRole:
    async def test_creates_role_successfully(self, service, repos):
        _configure_session_for_create(repos["role"].session)
        repos["role"].find_by_slug = AsyncMock(return_value=None)
        repos["role"].find_by_name = AsyncMock(return_value=None)
        data = RoleCreateRequest(name="Manager", description="Custom manager role")
        result = await service.create_role(data, organization_id=uuid.uuid4())
        assert result.name == "Manager"

    async def test_raises_on_duplicate_slug(self, service, repos):
        repos["role"].find_by_slug = AsyncMock(return_value=_make_role())
        data = RoleCreateRequest(name="Admin")
        with pytest.raises(DuplicateRoleError):
            await service.create_role(data)

    async def test_creates_global_role(self, service, repos):
        _configure_session_for_create(repos["role"].session)
        repos["role"].find_by_slug = AsyncMock(return_value=None)
        repos["role"].find_by_name = AsyncMock(return_value=None)
        data = RoleCreateRequest(name="Global Role")
        result = await service.create_role(data)
        assert result.name == "Global Role"


class TestUpdateRole:
    async def test_updates_role(self, service, repos):
        role = _make_role()
        repos["role"].get_by_id = AsyncMock(return_value=role)
        data = RoleUpdateRequest(description="Updated description")
        result = await service.update_role(role.id, data)
        assert result is not None

    async def test_raises_on_system_role(self, service, repos):
        role = _make_role(is_system_role=True)
        repos["role"].get_by_id = AsyncMock(return_value=role)
        data = RoleUpdateRequest(description="try")
        with pytest.raises(SystemRoleModificationError):
            await service.update_role(role.id, data)


class TestDeleteRole:
    async def test_deletes_custom_role(self, service, repos):
        role = _make_role()
        repos["role"].get_by_id = AsyncMock(return_value=role)
        await service.delete_role(role.id)
        repos["role"].soft_delete.assert_awaited_once_with(role.id)

    async def test_raises_on_system_role(self, service, repos):
        role = _make_role(is_system_role=True)
        repos["role"].get_by_id = AsyncMock(return_value=role)
        with pytest.raises(SystemRoleModificationError):
            await service.delete_role(role.id)


class TestCreatePermission:
    async def test_creates_permission(self, service, repos):
        _configure_session_for_create(repos["perm"].session)
        repos["perm"].find_by_code = AsyncMock(return_value=None)
        data = PermissionCreateRequest(resource="supplier", action="read")
        result = await service.create_permission(data)
        assert result.code == "supplier.read"

    async def test_raises_on_duplicate(self, service, repos):
        repos["perm"].find_by_code = AsyncMock(return_value=_make_permission())
        data = PermissionCreateRequest(resource="purchase", action="create")
        with pytest.raises(DuplicatePermissionError):
            await service.create_permission(data)


class TestAssignPermissionsToRole:
    async def test_assigns_permissions(self, service, repos):
        role = _make_role()
        repos["role"].get_by_id = AsyncMock(return_value=role)
        repos["rp"].assign_many = AsyncMock(
            return_value=[MagicMock(permission_id=uuid.uuid4())],
        )
        data = AssignPermissionRequest(permission_ids=[uuid.uuid4()])
        result = await service.assign_permissions_to_role(role.id, data)
        assert len(result) == 1

    async def test_raises_on_system_role(self, service, repos):
        role = _make_role(is_system_role=True)
        repos["role"].get_by_id = AsyncMock(return_value=role)
        data = AssignPermissionRequest(permission_ids=[uuid.uuid4()])
        with pytest.raises(SystemRoleModificationError):
            await service.assign_permissions_to_role(role.id, data)


class TestAssignRolesToMembership:
    async def test_assigns_roles(self, service, repos):
        repos["mr"].assign_many = AsyncMock(
            return_value=[_make_membership_role()],
        )
        data = AssignRoleRequest(role_ids=[uuid.uuid4()])
        result = await service.assign_roles_to_membership(uuid.uuid4(), data)
        assert len(result) == 1


class TestAuthorizationChecks:
    async def test_can_returns_true(self, service, repos):
        repos["mr"].has_permission = AsyncMock(return_value=True)
        result = await service.can(uuid.uuid4(), "purchase.read")
        assert result is True

    async def test_can_returns_false(self, service, repos):
        repos["mr"].has_permission = AsyncMock(return_value=False)
        result = await service.can(uuid.uuid4(), "purchase.read")
        assert result is False

    async def test_can_any_returns_true(self, service, repos):
        repos["mr"].has_any_permission = AsyncMock(return_value=True)
        result = await service.can_any(
            uuid.uuid4(), ["purchase.read", "supplier.read"],
        )
        assert result is True

    async def test_can_all_returns_true(self, service, repos):
        repos["mr"].has_all_permissions = AsyncMock(return_value=True)
        result = await service.can_all(
            uuid.uuid4(), ["purchase.read", "supplier.read"],
        )
        assert result is True

    async def test_check_permission_granted(self, service, repos):
        repos["mr"].has_permission = AsyncMock(return_value=True)
        result = await service.check_permission(uuid.uuid4(), "purchase.read")
        assert result.granted is True
        assert result.missing_permissions == []

    async def test_check_permission_denied(self, service, repos):
        repos["mr"].has_permission = AsyncMock(return_value=False)
        result = await service.check_permission(uuid.uuid4(), "purchase.read")
        assert result.granted is False
        assert "purchase.read" in result.missing_permissions

    async def test_get_current_permissions(self, service, repos):
        role = _make_role(name="Viewer")
        repos["mr"].get_active_roles_for_membership = AsyncMock(
            return_value=[_make_membership_role(role=role)],
        )
        repos["mr"].get_all_permissions_for_membership = AsyncMock(
            return_value={"purchase.read"},
        )
        result = await service.get_current_permissions(uuid.uuid4())
        assert "Viewer" in result.role_names
        assert "purchase.read" in result.permission_codes


class TestSeedSystemRoles:
    async def test_seeds_idempotently(self, service, repos):
        repos["role"].find_by_slug = AsyncMock(return_value=None)
        repos["perm"].find_by_code = AsyncMock(return_value=None)
        repos["rp"].get_by_role_and_permission = AsyncMock(return_value=None)
        await service.seed_system_roles()
        assert repos["role"].session.add.call_count > 0

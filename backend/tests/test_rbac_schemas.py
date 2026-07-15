from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.domains.rbac.schemas import (
    AssignPermissionRequest,
    AssignRoleRequest,
    PermissionCheckRequest,
    PermissionCreateRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
)


class TestRoleCreateRequest:
    def test_valid(self):
        data = RoleCreateRequest(name="Manager")
        assert data.name == "Manager"
        assert data.slug is None

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            RoleCreateRequest(name="")

    def test_too_long_name_raises(self):
        with pytest.raises(ValidationError):
            RoleCreateRequest(name="x" * 101)

    def test_with_all_fields(self):
        data = RoleCreateRequest(
            name="Custom Role", slug="custom_role",
            description="A custom role", priority=50,
            metadata={"source": "terraform"},
        )
        assert data.slug == "custom_role"
        assert data.priority == 50


class TestRoleUpdateRequest:
    def test_partial_update(self):
        data = RoleUpdateRequest(name="New Name")
        assert data.name == "New Name"
        assert data.description is None

    def test_empty_update(self):
        data = RoleUpdateRequest()
        assert data.model_dump(exclude_unset=True) == {}


class TestPermissionCreateRequest:
    def test_valid(self):
        data = PermissionCreateRequest(resource="purchase", action="create")
        assert data.resource == "purchase"
        assert data.action == "create"

    def test_invalid_resource_pattern(self):
        with pytest.raises(ValidationError):
            PermissionCreateRequest(resource="Purchase Order", action="create")

    def test_invalid_action_pattern(self):
        with pytest.raises(ValidationError):
            PermissionCreateRequest(resource="purchase", action="Create")


class TestAssignPermissionRequest:
    def test_valid(self):
        pid = uuid.uuid4()
        data = AssignPermissionRequest(permission_ids=[pid])
        assert data.permission_ids == [pid]

    def test_empty_list_raises(self):
        with pytest.raises(ValidationError):
            AssignPermissionRequest(permission_ids=[])


class TestAssignRoleRequest:
    def test_valid(self):
        rid = uuid.uuid4()
        data = AssignRoleRequest(role_ids=[rid])
        assert data.role_ids == [rid]

    def test_empty_list_raises(self):
        with pytest.raises(ValidationError):
            AssignRoleRequest(role_ids=[])


class TestPermissionCheckRequest:
    def test_valid(self):
        data = PermissionCheckRequest(permission_codes=["purchase.read"])
        assert data.permission_codes == ["purchase.read"]

    def test_empty_list_raises(self):
        with pytest.raises(ValidationError):
            PermissionCheckRequest(permission_codes=[])

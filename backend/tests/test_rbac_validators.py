from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.domains.rbac.exceptions import (
    DuplicatePermissionError,
    DuplicateRoleError,
    PermissionNotFoundError,
    RoleNotFoundError,
    SystemRoleModificationError,
)
from app.domains.rbac.validators import (
    check_duplicate_permission,
    check_duplicate_role,
    check_permission_exists,
    check_role_exists,
    ensure_not_system_role,
    validate_permission_code,
    validate_role_name,
    validate_slug,
)


class TestValidateRoleName:
    def test_valid(self):
        assert validate_role_name("Procurement Manager") == "Procurement Manager"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_role_name("  ")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="cannot exceed 100"):
            validate_role_name("x" * 101)


class TestValidateSlug:
    def test_valid(self):
        assert validate_slug("Procurement Manager") == "procurement_manager"

    def test_strips_and_lowers(self):
        assert validate_slug("  Admin  ") == "admin"

    def test_invalid_chars_raises(self):
        with pytest.raises(ValueError, match="Slug must start"):
            validate_slug("123abc")


class TestValidatePermissionCode:
    def test_joins_resource_and_action(self):
        assert validate_permission_code("purchase", "create") == "purchase.create"


class TestCheckDuplicateRole:
    def test_raises_when_role_exists(self):
        role = MagicMock(name="Admin")
        with pytest.raises(DuplicateRoleError):
            check_duplicate_role(role, name="Admin")

    def test_passes_when_none(self):
        check_duplicate_role(None, name="Admin")


class TestCheckDuplicatePermission:
    def test_raises_when_exists(self):
        perm = MagicMock(code="purchase.create")
        with pytest.raises(DuplicatePermissionError):
            check_duplicate_permission(perm, "purchase.create")

    def test_passes_when_none(self):
        check_duplicate_permission(None, "purchase.create")


class TestCheckRoleExists:
    def test_returns_role_when_found(self):
        role = MagicMock()
        result = check_role_exists(role, str(uuid.uuid4()))
        assert result is role

    def test_raises_when_none(self):
        with pytest.raises(RoleNotFoundError):
            check_role_exists(None, str(uuid.uuid4()))


class TestCheckPermissionExists:
    def test_returns_perm_when_found(self):
        perm = MagicMock()
        result = check_permission_exists(perm, str(uuid.uuid4()))
        assert result is perm

    def test_raises_when_none(self):
        with pytest.raises(PermissionNotFoundError):
            check_permission_exists(None, str(uuid.uuid4()))


class TestEnsureNotSystemRole:
    def test_raises_for_system_role(self):
        role = MagicMock(is_system_role=True, name="Owner")
        with pytest.raises(SystemRoleModificationError):
            ensure_not_system_role(role, "delete")

    def test_passes_for_custom_role(self):
        role = MagicMock(is_system_role=False)
        ensure_not_system_role(role, "delete")


from __future__ import annotations

from enum import StrEnum


class SystemRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    PROCUREMENT_MANAGER = "procurement_manager"
    PROCUREMENT_ANALYST = "procurement_analyst"
    FINANCE_APPROVER = "finance_approver"
    VIEWER = "viewer"


"""
SystemRole defines the built-in roles that every organization gets automatically.

OWNER:
  - Full access to everything within the organization.
  - Can manage billing, delete the organization, transfer ownership.
  - Cannot be removed by anyone.
  - Always present — every org must have exactly one owner at all times.

ADMIN:
  - Full administrative access except billing/org deletion.
  - Can manage roles, permissions, members, and all data.
  - Can promote/demote non-owner members.

PROCUREMENT_MANAGER:
  - Can create, read, update, and delete procurement entities.
  - Can approve/reject purchase requests up to a spending limit.
  - Manages suppliers, contracts, purchase orders.

PROCUREMENT_ANALYST:
  - Read access to all procurement data for reporting/analysis.
  - Can generate reports, view dashboards, export data.
  - Cannot modify or approve any procurement operation.

FINANCE_APPROVER:
  - Read access to procurement data.
  - Can approve purchase requests and invoices.
  - Cannot create or modify suppliers/contracts.

VIEWER:
  - Read-only access to all non-sensitive data.
  - Cannot modify or approve anything.

Why system roles exist:
  - Eliminate bootstrapping: every new org immediately has a complete
    authorization model without manually creating roles.
  - Guarantee invariants: the Owner role is always present, preventing
    orgs from becoming unmanageable.
  - Framework for upgrades: system permissions are additive only,
    ensuring upgrades never break existing assignments.
"""


class PermissionCategory(StrEnum):
    ORGANIZATION = "organization"
    USER = "user"
    MEMBERSHIP = "membership"
    ROLE = "role"
    PERMISSION = "permission"
    SUPPLIER = "supplier"
    CONTRACT = "contract"
    PURCHASE = "purchase"
    INVOICE = "invoice"
    DOCUMENT = "document"
    SYSTEM = "system"


"""
PermissionCategory groups permissions by functional domain.

This enables:
  - UI grouping (show all "supplier" permissions together)
  - Bulk operations (grant all "purchase" permissions)
  - Audit categorization (what areas did this user access?)
  - Future AI reasoning (which domain does this action belong to?)

Each future module registers its own category without modifying
the authorization engine — the engine treats category as metadata.

Categories are not enforced at the database level; they are a
convention that the UI, audit system, and AI use for organization.
"""

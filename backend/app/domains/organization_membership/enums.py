from __future__ import annotations

from enum import StrEnum


class MembershipStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LEFT = "left"
    REMOVED = "removed"
    REJECTED = "rejected"
    EXPIRED = "expired"


"""
MembershipStatus lifecycle:

    Invite sent
        │
    ┌───▼───┐
    │PENDING│────────────────────┐
    └───┬───┘                    │
        │                        │
    ┌───▼───┐              ┌─────▼──────┐
    │ACTIVE │◄──accept─────│  EXPIRED   │ (invitation expired)
    └───┬───┘              └────────────┘
        │
    ┌───▼──────┐     ┌──────┐
    │SUSPENDED │────►│ LEFT │ (user leaves)
    └──────────┘     └──────┘
        │
    ┌───▼────┐
    │ REMOVED│ (admin removes)
    └────────┘

    REJECTED (user rejects invitation - terminal)

Transitions (future enforcement):
    PENDING   → ACTIVE, EXPIRED, REJECTED
    ACTIVE    → SUSPENDED, LEFT
    SUSPENDED → ACTIVE (restore), REMOVED
    LEFT      → (terminal, re-invite required)
    REMOVED   → (terminal, re-invite required)
    REJECTED  → (terminal, re-invite required)
    EXPIRED   → (terminal, re-invite required)
"""

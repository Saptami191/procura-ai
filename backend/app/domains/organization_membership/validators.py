from __future__ import annotations

from app.domains.organization_membership.enums import MembershipStatus

ALLOWED_TRANSITIONS: dict[MembershipStatus, set[MembershipStatus]] = {
    MembershipStatus.PENDING: {
        MembershipStatus.ACTIVE,
        MembershipStatus.REJECTED,
        MembershipStatus.EXPIRED,
    },
    MembershipStatus.ACTIVE: {
        MembershipStatus.SUSPENDED,
        MembershipStatus.LEFT,
    },
    MembershipStatus.SUSPENDED: {
        MembershipStatus.ACTIVE,
        MembershipStatus.REMOVED,
    },
    MembershipStatus.LEFT: set(),
    MembershipStatus.REMOVED: set(),
    MembershipStatus.REJECTED: set(),
    MembershipStatus.EXPIRED: set(),
}


def validate_status_transition(
    current: MembershipStatus,
    target: MembershipStatus,
) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ValueError(
            f"Cannot transition from '{current.value}' to '{target.value}'. "
            "Allowed targets from '{}': {}".format(
                current.value,
                ", ".join(s.value for s in allowed) or "(none)",
            )
        )


def validate_invite_payload(data: dict) -> dict:
    validated: dict = {}
    if "user_id" in data:
        validated["user_id"] = data["user_id"]
    if "is_owner" in data:
        validated["is_owner"] = bool(data["is_owner"])
    return validated


def validate_update_payload(data: dict) -> dict:
    validated: dict = {}
    if "is_owner" in data and data["is_owner"] is not None:
        validated["is_owner"] = bool(data["is_owner"])
    if "is_default" in data and data["is_default"] is not None:
        validated["is_default"] = bool(data["is_default"])
    if "metadata" in data and data["metadata"] is not None:
        validated["metadata"] = data["metadata"]
    return validated

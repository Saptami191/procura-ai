from __future__ import annotations

import re
from typing import Any

from .enums import OrganizationStatus, SubscriptionPlan
from .exceptions import OrganizationValidationError

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WEBSITE_PATTERN = re.compile(
    r"^https?:\/\/([\w-]+\.)+[\w-]+(\/[\w\-\.~:/?#\[\]@!$&'()*+,;=]*)?$"
)
COUNTRY_PATTERN = re.compile(r"^[A-Z]{2}$")
TIMEZONE_PATTERN = re.compile(
    r"^[A-Za-z_]+\/[A-Za-z_]+(?:\/[A-Za-z_]+)?$"
)


def validate_name(name: str, field: str = "name") -> str:
    name = name.strip()
    if len(name) < 2:
        raise OrganizationValidationError(
            message=f"{field} must be at least 2 characters",
            details={field: name},
        )
    if len(name) > 255:
        raise OrganizationValidationError(
            message=f"{field} must not exceed 255 characters",
            details={field: name},
        )
    return name


def validate_slug(slug: str) -> str:
    slug = slug.strip().lower()
    if len(slug) < 2:
        raise OrganizationValidationError(
            message="Slug must be at least 2 characters",
            details={"slug": slug},
        )
    if len(slug) > 100:
        raise OrganizationValidationError(
            message="Slug must not exceed 100 characters",
            details={"slug": slug},
        )
    if not SLUG_PATTERN.match(slug):
        raise OrganizationValidationError(
            message="Slug must contain only lowercase letters, numbers, and hyphens",
            details={"slug": slug, "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$"},
        )
    return slug


def validate_website(website: str | None) -> str | None:
    if website is None:
        return None
    website = website.strip()
    if not WEBSITE_PATTERN.match(website):
        raise OrganizationValidationError(
            message="Invalid website URL format",
            details={"website": website},
        )
    if len(website) > 2048:
        raise OrganizationValidationError(
            message="Website URL must not exceed 2048 characters",
            details={"website": website},
        )
    return website


def validate_country(country: str | None) -> str | None:
    if country is None:
        return None
    country = country.strip().upper()
    if not COUNTRY_PATTERN.match(country):
        raise OrganizationValidationError(
            message="Country must be a valid ISO 3166-1 alpha-2 code",
            details={"country": country},
        )
    return country


def validate_timezone(timezone: str | None) -> str | None:
    if timezone is None:
        return None
    timezone = timezone.strip()
    if not TIMEZONE_PATTERN.match(timezone):
        raise OrganizationValidationError(
            message="Invalid timezone format. Use IANA timezone (e.g., America/New_York)",
            details={"timezone": timezone},
        )
    return timezone


def validate_company_size(size: int | None) -> int | None:
    if size is None:
        return None
    if size < 1:
        raise OrganizationValidationError(
            message="Company size must be at least 1",
            details={"company_size": size},
        )
    if size > 10_000_000:
        raise OrganizationValidationError(
            message="Company size seems unrealistic",
            details={"company_size": size},
        )
    return size


def validate_status(value: str) -> OrganizationStatus:
    try:
        return OrganizationStatus(value.lower())
    except ValueError:
        valid = [s.value for s in OrganizationStatus]
        raise OrganizationValidationError(
            message=f"Invalid status. Must be one of: {', '.join(valid)}",
            details={"status": value, "valid_values": valid},
        )


def validate_plan(value: str) -> SubscriptionPlan:
    try:
        return SubscriptionPlan(value.lower())
    except ValueError:
        valid = [p.value for p in SubscriptionPlan]
        raise OrganizationValidationError(
            message=f"Invalid subscription plan. Must be one of: {', '.join(valid)}",
            details={"plan": value, "valid_values": valid},
        )


def generate_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    if not slug:
        slug = "org"
    return slug


def validate_create_payload(data: dict[str, Any]) -> dict[str, Any]:
    validated: dict[str, Any] = {}
    validated["name"] = validate_name(data.get("name", ""))
    if "slug" in data and data["slug"]:
        validated["slug"] = validate_slug(data["slug"])
    else:
        validated["slug"] = generate_slug(validated["name"])
    if "description" in data:
        validated["description"] = data["description"]
    if "industry" in data:
        validated["industry"] = data["industry"]
    if "company_size" in data:
        validated["company_size"] = validate_company_size(data["company_size"])
    if "country" in data:
        validated["country"] = validate_country(data.get("country"))
    if "timezone" in data:
        validated["timezone"] = validate_timezone(data.get("timezone"))
    if "website" in data:
        validated["website"] = validate_website(data.get("website"))
    if "logo_url" in data:
        validated["logo_url"] = data["logo_url"]
    if "status" in data and data["status"]:
        validated["status"] = validate_status(data["status"])
    if "subscription_plan" in data and data["subscription_plan"]:
        validated["subscription_plan"] = validate_plan(data["subscription_plan"])
    return validated


def validate_update_payload(data: dict[str, Any]) -> dict[str, Any]:
    validated: dict[str, Any] = {}
    if "name" in data and data["name"] is not None:
        validated["name"] = validate_name(data["name"])
    if "slug" in data and data["slug"] is not None:
        validated["slug"] = validate_slug(data["slug"])
    if "description" in data:
        validated["description"] = data["description"]
    if "industry" in data:
        validated["industry"] = data["industry"]
    if "company_size" in data:
        validated["company_size"] = validate_company_size(data["company_size"])
    if "country" in data:
        validated["country"] = validate_country(data.get("country"))
    if "timezone" in data:
        validated["timezone"] = validate_timezone(data.get("timezone"))
    if "website" in data:
        validated["website"] = validate_website(data.get("website"))
    if "logo_url" in data:
        validated["logo_url"] = data["logo_url"]
    if "status" in data and data["status"] is not None:
        validated["status"] = validate_status(data["status"])
    if "subscription_plan" in data and data["subscription_plan"] is not None:
        validated["subscription_plan"] = validate_plan(data["subscription_plan"])
    if "is_active" in data and data["is_active"] is not None:
        validated["is_active"] = bool(data["is_active"])
    return validated

from __future__ import annotations

import re

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_](?:[a-zA-Z0-9_.-]{0,253}[a-zA-Z0-9_])?$")
PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{6,14}$")
COUNTRY_CODE_PATTERN = re.compile(r"^[a-z]{2,3}(?:-[A-Z]{2})?$")
TIMEZONE_PATTERN = re.compile(
    r"^[A-Za-z_]+\/[A-Za-z_]+(?:\/[A-Za-z_]+)?$"
)
DISPLAY_NAME_PATTERN = re.compile(r"^[^\s].*[^\s]$|^[^\s]$")


def validate_email(email: str) -> str:
    email = email.strip().lower()
    if len(email) > 255:
        raise ValueError("Email must not exceed 255 characters")
    return email


def validate_username(username: str) -> str:
    username = username.strip()
    if len(username) < 2:
        raise ValueError("Username must be at least 2 characters")
    if len(username) > 255:
        raise ValueError("Username must not exceed 255 characters")
    if not USERNAME_PATTERN.match(username):
        raise ValueError(
            "Username can only contain letters, numbers, dots, hyphens, and underscores"
        )
    return username


def validate_display_name(name: str) -> str:
    name = name.strip()
    if len(name) < 1:
        raise ValueError("Display name cannot be empty")
    if len(name) > 255:
        raise ValueError("Display name must not exceed 255 characters")
    return name


def validate_phone(phone: str) -> str:
    phone = phone.strip()
    if not PHONE_PATTERN.match(phone):
        raise ValueError("Invalid phone number format. Use E.164 format (e.g., +1234567890)")
    return phone


def validate_country_code(code: str) -> str:
    code = code.strip()
    if not COUNTRY_CODE_PATTERN.match(code):
        raise ValueError(
            "Invalid language code format. Use ISO 639-1 or BCP 47 (e.g., 'en' or 'en-US')"
        )
    return code


def validate_timezone(timezone: str) -> str:
    timezone = timezone.strip()
    if not TIMEZONE_PATTERN.match(timezone):
        raise ValueError("Invalid timezone format. Use IANA timezone (e.g., America/New_York)")
    return timezone


def validate_update_payload(data: dict) -> dict:
    validated: dict = {}
    if "email" in data and data["email"] is not None:
        validated["email"] = validate_email(data["email"])
    if "username" in data and data["username"] is not None:
        validated["username"] = validate_username(data["username"])
    if "display_name" in data and data["display_name"] is not None:
        validated["display_name"] = validate_display_name(data["display_name"])
    if "phone" in data and data["phone"] is not None:
        validated["phone"] = validate_phone(data["phone"])
    if "preferred_language" in data and data["preferred_language"] is not None:
        validated["preferred_language"] = validate_country_code(data["preferred_language"])
    if "timezone" in data and data["timezone"] is not None:
        validated["timezone"] = validate_timezone(data["timezone"])
    if "full_name" in data:
        validated["full_name"] = data["full_name"]
    if "profile_image_url" in data:
        validated["profile_image_url"] = data["profile_image_url"]
    if "job_title" in data:
        validated["job_title"] = data["job_title"]
    if "department" in data:
        validated["department"] = data["department"]
    if "is_active" in data and data["is_active"] is not None:
        validated["is_active"] = bool(data["is_active"])
    if "is_superuser" in data and data["is_superuser"] is not None:
        validated["is_superuser"] = bool(data["is_superuser"])
    return validated

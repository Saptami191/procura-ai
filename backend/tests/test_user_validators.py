from __future__ import annotations

import pytest

from app.domains.user.validators import (
    validate_country_code,
    validate_display_name,
    validate_email,
    validate_phone,
    validate_timezone,
    validate_update_payload,
    validate_username,
)


class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email("Test@Example.COM") == "test@example.com"

    def test_invalid_email_too_long(self):
        with pytest.raises(ValueError):
            validate_email("a" * 256 + "@b.com")

    def test_empty_email_strips_and_lowers(self):
        result = validate_email("  USER@Example.COM  ")
        assert result == "user@example.com"


class TestValidateUsername:
    def test_valid_username(self):
        assert validate_username("john_doe-123") == "john_doe-123"

    def test_too_short(self):
        with pytest.raises(ValueError):
            validate_username("a")

    def test_too_long(self):
        with pytest.raises(ValueError):
            validate_username("a" * 256)

    def test_invalid_characters(self):
        with pytest.raises(ValueError):
            validate_username("user name!")

    def test_strips_whitespace(self):
        assert validate_username("  valid_user  ") == "valid_user"

    def test_dots_allowed(self):
        assert validate_username("john.doe") == "john.doe"

    def test_hyphens_allowed(self):
        assert validate_username("john-doe") == "john-doe"

    def test_underscores_allowed(self):
        assert validate_username("john_doe") == "john_doe"

    def test_leading_dot_invalid(self):
        with pytest.raises(ValueError):
            validate_username(".invalid")


class TestValidateDisplayName:
    def test_valid_name(self):
        assert validate_display_name("John Doe") == "John Doe"

    def test_too_long(self):
        with pytest.raises(ValueError):
            validate_display_name("J" * 256)

    def test_leading_trailing_whitespace_stripped(self):
        assert validate_display_name("  John  ") == "John"


class TestValidatePhone:
    def test_valid_international(self):
        assert validate_phone("+1234567890") == "+1234567890"

    def test_valid_without_plus(self):
        assert validate_phone("1234567890") == "1234567890"

    def test_too_short(self):
        with pytest.raises(ValueError):
            validate_phone("+123")

    def test_contains_letters(self):
        with pytest.raises(ValueError):
            validate_phone("+1234ABC890")

    def test_strips_whitespace(self):
        assert validate_phone("  +1234567890  ") == "+1234567890"


class TestValidateCountryCode:
    def test_valid_two_letter(self):
        assert validate_country_code("en") == "en"

    def test_valid_with_region(self):
        assert validate_country_code("en-US") == "en-US"

    def test_invalid_code(self):
        with pytest.raises(ValueError):
            validate_country_code("english")

    def test_strips_whitespace(self):
        assert validate_country_code("  fr  ") == "fr"


class TestValidateTimezone:
    def test_valid_timezone(self):
        assert validate_timezone("America/New_York") == "America/New_York"

    def test_multi_segment(self):
        tz = "America/Argentina/Buenos_Aires"
        assert validate_timezone(tz) == tz

    def test_invalid_timezone(self):
        with pytest.raises(ValueError):
            validate_timezone("invalid")

    def test_strips_whitespace(self):
        assert validate_timezone("  Europe/London  ") == "Europe/London"


class TestValidateUpdatePayload:
    def test_empty_payload(self):
        assert validate_update_payload({}) == {}

    def test_valid_email_in_payload(self):
        result = validate_update_payload({"email": "Test@Example.com"})
        assert result["email"] == "test@example.com"

    def test_phone_validation(self):
        result = validate_update_payload({"phone": "+1234567890"})
        assert result["phone"] == "+1234567890"

    def test_none_values_not_keyed(self):
        result = validate_update_payload({"email": None, "username": None})
        assert "email" not in result
        assert "username" not in result

    def test_full_name_passthrough(self):
        result = validate_update_payload({"full_name": "John Doe"})
        assert result["full_name"] == "John Doe"

    def test_boolean_coercion(self):
        result = validate_update_payload({"is_active": 1, "is_superuser": 0})
        assert result["is_active"] is True
        assert result["is_superuser"] is False

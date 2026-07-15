from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.dependencies import get_auth_service
from app.auth.schemas import TokenResponse
from app.auth.service import AuthService
from app.domains.user.dependencies import get_current_user_model, get_user_service
from app.domains.user.models import User
from app.domains.user.service import UserService
from app.main import app


@pytest.fixture
def mock_auth_service():
    service = MagicMock(spec=AuthService)
    service.create_session = AsyncMock()
    service.create_token_pair = AsyncMock()
    service.record_login_attempt = AsyncMock()
    service.refresh = AsyncMock()
    service.logout = AsyncMock()
    return service


@pytest.fixture
def mock_user_service():
    service = MagicMock(spec=UserService)
    service.verify_credentials = AsyncMock()
    return service


@pytest.fixture
def client(mock_auth_service, mock_user_service):
    # Setup dependency overrides
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    yield TestClient(app)
    # Clear overrides
    app.dependency_overrides.clear()


def test_login_success(client, mock_auth_service, mock_user_service):
    # Arrange
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.email = "test@example.com"
    mock_user_service.verify_credentials.return_value = mock_user

    mock_session = MagicMock()
    mock_session.id = session_id
    mock_auth_service.create_session.return_value = mock_session

    mock_auth_service.create_token_pair.return_value = TokenResponse(
        access_token="mock_access",
        refresh_token="mock_refresh",
        token_type="bearer",
        expires_in=900,
    )

    # Act
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["access_token"] == "mock_access"
    assert data["refresh_token"] == "mock_refresh"
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900

    mock_user_service.verify_credentials.assert_called_once_with(
        "test@example.com", "password123"
    )
    mock_auth_service.create_session.assert_called_once_with(
        user_id=user_id,
        ip_address="testclient",
        user_agent="testclient",
    )
    mock_auth_service.create_token_pair.assert_called_once_with(
        user_id=user_id,
        session_id=session_id,
        ip_address="testclient",
    )
    mock_auth_service.record_login_attempt.assert_any_call(
        email="test@example.com",
        success=True,
        user_id=user_id,
        ip_address="testclient",
        user_agent="testclient",
    )


def test_login_failure(client, mock_auth_service, mock_user_service):
    # Arrange
    mock_user_service.verify_credentials.return_value = None

    # Act
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrong_password"},
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "detail" in data or "message" in data  # depending on exception handlers format

    mock_auth_service.record_login_attempt.assert_called_once_with(
        email="test@example.com",
        success=False,
        ip_address="testclient",
        user_agent="testclient",
        failure_reason="Invalid credentials",
    )


def test_refresh_success(client, mock_auth_service):
    # Arrange
    mock_auth_service.refresh.return_value = TokenResponse(
        access_token="new_access",
        refresh_token="new_refresh",
        token_type="bearer",
        expires_in=900,
    )

    # Act
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "old_refresh"},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["access_token"] == "new_access"
    assert data["refresh_token"] == "new_refresh"
    mock_auth_service.refresh.assert_called_once_with("old_refresh")


def test_logout_success(client, mock_auth_service):
    # Act
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "token_to_revoke"},
    )

    # Assert
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_auth_service.logout.assert_called_once_with("token_to_revoke")


def test_me_success(mock_auth_service, mock_user_service):
    # Arrange
    user_id = uuid.uuid4()
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.email = "test@example.com"
    mock_user.username = "testuser"
    mock_user.full_name = "Test User"
    mock_user.display_name = "Test User"
    mock_user.profile_image_url = None
    mock_user.phone = None
    mock_user.job_title = None
    mock_user.department = None
    mock_user.preferred_language = "en"
    mock_user.timezone = "UTC"
    mock_user.is_active = True
    mock_user.is_superuser = False
    mock_user.email_verified = True
    mock_user.phone_verified = False
    mock_user.last_login_at = None
    mock_user.created_at = datetime.now(UTC)
    mock_user.updated_at = datetime.now(UTC)

    app.dependency_overrides[get_current_user_model] = lambda: mock_user
    client = TestClient(app)

    # Act
    response = client.get("/api/v1/auth/me")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(user_id)
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"

    app.dependency_overrides.clear()

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from app.auth.dependencies import get_auth_service, get_current_user
from app.auth.exceptions import InvalidCredentialsException
from app.auth.schemas import (
    CurrentUser,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshRequest,
    RefreshResponse,
)
from app.auth.service import AuthService
from app.domains.user.dependencies import get_current_user_model, get_user_service
from app.domains.user.models import User
from app.domains.user.schemas import CurrentUserResponse
from app.domains.user.service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    request: Request,
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
) -> LoginResponse:
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user = await user_service.verify_credentials(data.email, data.password)
    if user is None:
        # Record failed attempt
        await auth_service.record_login_attempt(
            email=data.email,
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason="Invalid credentials",
        )
        raise InvalidCredentialsException()

    # Successful login
    session = await auth_service.create_session(
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    token_pair = await auth_service.create_token_pair(
        user_id=user.id,
        session_id=session.id,
        ip_address=ip_address,
    )

    await auth_service.record_login_attempt(
        email=data.email,
        success=True,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return LoginResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh(
    data: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> RefreshResponse:
    token_pair = await auth_service.refresh(data.refresh_token)
    return RefreshResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    data: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    await auth_service.logout(data.refresh_token)


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
)
async def me(
    current_user: User = Depends(get_current_user_model),
) -> User:
    return current_user

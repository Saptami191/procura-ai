from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_token
from app.auth.repository import (
    LoginAttemptRepository,
    RefreshTokenRepository,
    SessionRepository,
)
from app.auth.schemas import CurrentUser
from app.auth.service import AuthService
from app.db.dependencies import get_db

_security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from e

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return CurrentUser(id=uuid.UUID(sub), is_authenticated=True)


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if not current_user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
        )
    return current_user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security_scheme),
) -> CurrentUser | None:
    if credentials is None:
        return None

    try:
        payload = decode_token(credentials.credentials)
        sub = payload.get("sub")
        if sub:
            return CurrentUser(id=uuid.UUID(sub), is_authenticated=True)
    except Exception:
        return None

    return None


async def get_refresh_token_repository(
    session: AsyncSession = Depends(get_db),
) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


async def get_session_repository(
    session: AsyncSession = Depends(get_db),
) -> SessionRepository:
    return SessionRepository(session)


async def get_login_attempt_repository(
    session: AsyncSession = Depends(get_db),
) -> LoginAttemptRepository:
    return LoginAttemptRepository(session)


async def get_auth_service(
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
    login_attempt_repo: LoginAttemptRepository = Depends(get_login_attempt_repository),
) -> AuthService:
    return AuthService(refresh_token_repo, session_repo, login_attempt_repo)


from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from loguru import logger

from app.auth.exceptions import (
    ExpiredTokenException,
    InactiveSessionException,
    InvalidTokenException,
    RevokedTokenException,
)
from app.auth.jwt import create_access_token
from app.auth.models import LoginAttempt, RefreshToken, Session
from app.auth.repository import (
    LoginAttemptRepository,
    RefreshTokenRepository,
    SessionRepository,
)
from app.auth.schemas import TokenResponse
from app.auth.utils import generate_refresh_token, hash_refresh_token
from app.core import settings


class AuthService:
    def __init__(
        self,
        refresh_token_repo: RefreshTokenRepository,
        session_repo: SessionRepository,
        login_attempt_repo: LoginAttemptRepository,
    ) -> None:
        self._refresh_token_repo = refresh_token_repo
        self._session_repo = session_repo
        self._login_attempt_repo = login_attempt_repo

    async def create_session(
        self,
        user_id: uuid.UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Session:
        now = datetime.now(UTC)
        session = Session(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            last_activity_at=now,
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
            is_active=True,
        )
        self._session_repo.session.add(session)
        await self._session_repo.session.flush()
        await self._session_repo.session.refresh(session)
        return session

    async def create_token_pair(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> TokenResponse:
        refresh_token_str = generate_refresh_token()
        token_hash = hash_refresh_token(refresh_token_str)

        refresh_token = RefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            session_id=session_id,
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.refresh_token_expire_days),
            created_by_ip=ip_address,
        )
        self._refresh_token_repo.session.add(refresh_token)
        await self._refresh_token_repo.session.flush()

        access_token = create_access_token(user_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def refresh(self, refresh_token_str: str) -> TokenResponse:
        token_hash = hash_refresh_token(refresh_token_str)
        stored = await self._refresh_token_repo.get_by_hash(token_hash)

        if stored is None:
            raise InvalidTokenException(details={"reason": "token not found"})

        if stored.revoked_at is not None:
            await self._revoke_rotation_chain(stored)
            raise RevokedTokenException(details={"reason": "token was previously revoked"})

        if stored.expires_at < datetime.now(UTC):
            raise ExpiredTokenException()

        session = await self._session_repo.get_active(stored.session_id)
        if session is None:
            raise InactiveSessionException()

        new_pair = await self.create_token_pair(
            user_id=stored.user_id,
            session_id=stored.session_id,
            ip_address=stored.created_by_ip,
        )

        await self._refresh_token_repo.revoke(stored.id, replaced_by=uuid.uuid4())
        await self._session_repo.update_activity(stored.session_id)

        return new_pair

    async def logout(self, refresh_token_str: str) -> None:
        token_hash = hash_refresh_token(refresh_token_str)
        stored = await self._refresh_token_repo.get_by_hash(token_hash)

        if stored is None:
            return

        await self._refresh_token_repo.revoke(stored.id)
        await self._session_repo.revoke(stored.session_id)

    async def logout_all_sessions(self, user_id: uuid.UUID) -> None:
        await self._session_repo.revoke_all_for_user(user_id)
        await self._refresh_token_repo.revoke_all_for_user(user_id)

    async def record_login_attempt(
        self,
        email: str,
        success: bool,
        user_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        failure_reason: str | None = None,
    ) -> None:
        attempt = LoginAttempt(
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason,
        )
        self._login_attempt_repo.session.add(attempt)
        await self._login_attempt_repo.session.flush()

        if not success:
            logger.warning(
                "Failed login attempt",
                email=email,
                ip=ip_address,
                reason=failure_reason,
            )

    async def _revoke_rotation_chain(self, token: RefreshToken) -> None:
        current = token
        while current is not None:
            if current.revoked_at is not None:
                break
            await self._refresh_token_repo.revoke(current.id)
            if current.replaced_by_token_id is None:
                break
            current = await self._refresh_token_repo.get_by_id(
                current.replaced_by_token_id, include_deleted=True
            )

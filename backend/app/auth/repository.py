from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update

from app.auth.models import LoginAttempt, RefreshToken, Session
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken, uuid.UUID]):
    model = RefreshToken

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        query = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def revoke(self, token_id: uuid.UUID, replaced_by: uuid.UUID | None = None) -> None:
        values: dict = {"revoked_at": datetime.utcnow()}
        if replaced_by:
            values["replaced_by_token_id"] = replaced_by
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(**values)
        )
        await self.session.execute(stmt)

    async def revoke_all_for_session(self, session_id: uuid.UUID) -> None:
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.session_id == session_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.utcnow())
        )
        await self.session.execute(stmt)

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.utcnow())
        )
        await self.session.execute(stmt)


class SessionRepository(BaseRepository[Session, uuid.UUID]):
    model = Session

    async def get_active(self, session_id: uuid.UUID) -> Session | None:
        query = select(Session).where(
            Session.id == session_id,
            Session.is_active == True,  # noqa: E712
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def update_activity(self, session_id: uuid.UUID) -> None:
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(last_activity_at=datetime.utcnow())
        )
        await self.session.execute(stmt)

    async def revoke(self, session_id: uuid.UUID) -> None:
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(is_active=False)
        )
        await self.session.execute(stmt)

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        stmt = (
            update(Session)
            .where(
                Session.user_id == user_id,
                Session.is_active == True,  # noqa: E712
            )
            .values(is_active=False)
        )
        await self.session.execute(stmt)


class LoginAttemptRepository(BaseRepository[LoginAttempt, uuid.UUID]):
    model = LoginAttempt

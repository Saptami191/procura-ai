from __future__ import annotations

import uuid

from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.users.models import User


class UserRepository(BaseRepository[User, uuid.UUID]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_nickname(self, nickname: str) -> User | None:
        query = select(User).where(User.nickname == nickname)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def email_exists(self, email: str) -> bool:
        query = select(User.id).where(User.email == email).limit(1)
        result = await self.session.execute(query)
        return result.scalars().first() is not None

    async def nickname_exists(self, nickname: str) -> bool:
        query = select(User.id).where(User.nickname == nickname).limit(1)
        result = await self.session.execute(query)
        return result.scalars().first() is not None

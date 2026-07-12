from __future__ import annotations

import uuid

from sqlalchemy import select

from app.domains.user.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, uuid.UUID]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_username(self, username: str) -> User | None:
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_phone(self, phone: str) -> User | None:
        query = select(User).where(User.phone == phone)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def email_exists(self, email: str) -> bool:
        query = select(User.id).where(User.email == email).limit(1)
        result = await self.session.execute(query)
        return result.scalars().first() is not None

    async def username_exists(self, username: str) -> bool:
        query = select(User.id).where(User.username == username).limit(1)
        result = await self.session.execute(query)
        return result.scalars().first() is not None

    async def phone_exists(self, phone: str) -> bool:
        query = select(User.id).where(User.phone == phone).limit(1)
        result = await self.session.execute(query)
        return result.scalars().first() is not None

    async def find_by_email_or_username(self, login: str) -> User | None:
        query = select(User).where(
            (User.email == login) | (User.username == login)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

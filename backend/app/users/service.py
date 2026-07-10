from __future__ import annotations

import uuid

from loguru import logger

from app.auth.password import hash_password, verify_password
from app.repositories.exceptions import DuplicateEntityError, EntityNotFoundError
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import UserCreate, UserRead, UserUpdate


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def create_user(self, data: UserCreate) -> UserRead:
        if await self._user_repo.email_exists(data.email):
            raise DuplicateEntityError(
                entity_name="User",
                fields={"email": data.email},
            )

        if data.nickname and await self._user_repo.nickname_exists(data.nickname):
            raise DuplicateEntityError(
                entity_name="User",
                fields={"nickname": data.nickname},
            )

        password_hash = hash_password(data.password)
        user = await self._user_repo.create(
            {
                "email": data.email,
                "password_hash": password_hash,
                "full_name": data.full_name,
                "nickname": data.nickname,
            }
        )

        logger.info("User created", user_id=str(user.id), email=user.email)
        return UserRead.model_validate(user)

    async def get_user(self, user_id: uuid.UUID) -> UserRead:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise EntityNotFoundError(entity_name="User", entity_id=str(user_id))
        return UserRead.model_validate(user)

    async def update_user(self, user_id: uuid.UUID, data: UserUpdate) -> UserRead:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise EntityNotFoundError(entity_name="User", entity_id=str(user_id))

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return UserRead.model_validate(user)

        if "nickname" in update_data and update_data["nickname"]:
            existing = await self._user_repo.get_by_nickname(update_data["nickname"])
            if existing and existing.id != user_id:
                raise DuplicateEntityError(
                    entity_name="User",
                    fields={"nickname": update_data["nickname"]},
                )

        updated = await self._user_repo.update(user_id, update_data)
        logger.info("User updated", user_id=str(user_id))
        return UserRead.model_validate(updated)

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise EntityNotFoundError(entity_name="User", entity_id=str(user_id))

        await self._user_repo.delete(user_id)
        logger.info("User deleted", user_id=str(user_id))

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[UserRead], int]:
        from app.repositories.pagination import Pagination

        pagination = Pagination(limit=limit, offset=skip)
        page = await self._user_repo.list(pagination=pagination)
        return (
            [UserRead.model_validate(u) for u in page.items],
            page.total,
        )

    async def get_by_email(self, email: str) -> User | None:
        return await self._user_repo.get_by_email(email)

    async def verify_credentials(self, email: str, password: str) -> User | None:
        user = await self._user_repo.get_by_email(email)
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

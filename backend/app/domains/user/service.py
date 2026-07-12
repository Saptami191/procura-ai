from __future__ import annotations

import uuid
from typing import Any

from loguru import logger

from app.auth.password import verify_password
from app.domains.user.exceptions import (
    DuplicateEmailError,
    DuplicatePhoneError,
    DuplicateUsernameError,
    InactiveUserError,
    UserNotFoundError,
)
from app.domains.user.mapper import UserMapper
from app.domains.user.models import User
from app.domains.user.repository import UserRepository
from app.domains.user.schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    UserSummary,
)
from app.domains.user.validators import validate_email
from app.repositories.exceptions import DuplicateEntityError, EntityNotFoundError


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def create_user(self, data: CreateUserRequest) -> UserResponse:
        email = validate_email(data.email)

        if await self._user_repo.email_exists(email):
            raise DuplicateEmailError(email)

        if data.username and await self._user_repo.username_exists(data.username):
            raise DuplicateUsernameError(data.username)

        if data.phone and await self._user_repo.phone_exists(data.phone):
            raise DuplicatePhoneError(data.phone)

        from app.auth.password import hash_password

        password_hash = hash_password(data.password)

        create_data: dict[str, Any] = {
            "email": email,
            "password_hash": password_hash,
            "username": data.username,
            "full_name": data.full_name,
            "display_name": data.display_name or data.full_name,
            "phone": data.phone,
            "job_title": data.job_title,
            "department": data.department,
            "preferred_language": data.preferred_language,
            "timezone": data.timezone,
        }

        try:
            user = await self._user_repo.create(create_data)
        except DuplicateEntityError as e:
            if "email" in str(e):
                raise DuplicateEmailError(str(data.email)) from e
            raise

        logger.info("User created", user_id=str(user.id), email=user.email)
        return UserMapper.to_response(user)

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id=str(user_id))
        return UserMapper.to_response(user)

    async def get_user_summary(self, user_id: uuid.UUID) -> UserSummary:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id=str(user_id))
        return UserMapper.to_summary(user)

    async def update_user(
        self, user_id: uuid.UUID, data: UpdateUserRequest
    ) -> UserResponse:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id=str(user_id))

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return UserMapper.to_response(user)

        if "username" in update_data and update_data["username"]:
            existing = await self._user_repo.get_by_username(
                update_data["username"]
            )
            if existing and existing.id != user_id:
                raise DuplicateUsernameError(update_data["username"])

        if "phone" in update_data and update_data["phone"]:
            existing = await self._user_repo.get_by_phone(
                update_data["phone"]
            )
            if existing and existing.id != user_id:
                raise DuplicatePhoneError(update_data["phone"])

        try:
            updated = await self._user_repo.update(user_id, update_data)
        except EntityNotFoundError as e:
            raise UserNotFoundError(user_id=str(user_id)) from e

        logger.info("User updated", user_id=str(user_id))
        return UserMapper.to_response(updated)

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id=str(user_id))

        await self._user_repo.delete(user_id)
        logger.info("User deleted", user_id=str(user_id))

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[UserSummary], int]:
        from app.repositories.pagination import Pagination

        pagination = Pagination(limit=limit, offset=skip)
        page = await self._user_repo.list(pagination=pagination)
        return (
            [UserMapper.to_summary(u) for u in page.items],
            page.total,
        )

    async def get_by_email(self, email: str) -> User | None:
        return await self._user_repo.get_by_email(email)

    async def verify_credentials(
        self, email: str, password: str
    ) -> User | None:
        user = await self._user_repo.get_by_email(email)
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    async def ensure_user_exists(self, user_id: uuid.UUID) -> User:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id=str(user_id))
        if not user.is_active:
            raise InactiveUserError(str(user_id))
        return user

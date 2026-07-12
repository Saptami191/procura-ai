from __future__ import annotations

from app.domains.user.models import User
from app.domains.user.schemas import (
    CurrentUserResponse,
    UserResponse,
    UserSummary,
)


class UserMapper:
    @staticmethod
    def to_response(user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    @staticmethod
    def to_summary(user: User) -> UserSummary:
        return UserSummary.model_validate(user)

    @staticmethod
    def to_current(user: User) -> CurrentUserResponse:
        return CurrentUserResponse.model_validate(user)

    @staticmethod
    def to_response_list(users: list[User]) -> list[UserResponse]:
        return [UserMapper.to_response(u) for u in users]

    @staticmethod
    def to_summary_list(users: list[User]) -> list[UserSummary]:
        return [UserMapper.to_summary(u) for u in users]

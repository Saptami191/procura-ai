from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.domains.user.dependencies import (
    get_current_user_model,
    get_user_service,
)
from app.domains.user.models import User
from app.domains.user.schemas import (
    CreateUserRequest,
    CurrentUserResponse,
    UpdateUserRequest,
    UserListResponse,
    UserResponse,
)
from app.domains.user.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: CreateUserRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.create_user(data)


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user_model),
) -> CurrentUserResponse:
    from app.domains.user.mapper import UserMapper

    return UserMapper.to_current(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    data: UpdateUserRequest,
    current_user: User = Depends(get_current_user_model),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.update_user(current_user.id, data)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.get_user(user_id)


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: UserService = Depends(get_user_service),
) -> UserListResponse:
    skip = (page - 1) * page_size
    users, total = await service.list_users(skip=skip, limit=page_size)
    return UserListResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, -(-total // page_size)),
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UpdateUserRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.update_user(user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    service: UserService = Depends(get_user_service),
) -> None:
    await service.delete_user(user_id)

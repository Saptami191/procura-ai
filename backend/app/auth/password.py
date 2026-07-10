from __future__ import annotations

from argon2 import PasswordHasher, Type
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

from app.core import settings

_hasher = PasswordHasher(
    time_cost=settings.password_argon2_time,
    memory_cost=settings.password_argon2_memory,
    parallelism=settings.password_argon2_parallelism,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except VerifyMismatchError:
        return False
    except (VerificationError, InvalidHashError):
        return False

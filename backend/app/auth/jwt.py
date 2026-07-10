from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from jwt import InvalidTokenError as PyJWTInvalidTokenError

from app.auth.exceptions import ExpiredTokenException, InvalidTokenException
from app.auth.utils import generate_token_id
from app.core import settings


def create_access_token(user_id: uuid.UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "jti": str(generate_token_id()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    return pyjwt.encode(
        payload,
        settings.resolved_jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict:
    try:
        return pyjwt.decode(
            token,
            settings.resolved_jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except PyJWTInvalidTokenError as e:
        error_str = str(e)
        if "expired" in error_str or "Expired" in error_str:
            raise ExpiredTokenException() from e
        raise InvalidTokenException(details={"error": error_str}) from e


def get_token_claims(token: str) -> dict:
    return decode_token(token)


def get_token_subject(token: str) -> str:
    payload = decode_token(token)
    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenException(details={"reason": "missing sub claim"})
    return sub

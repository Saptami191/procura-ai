from __future__ import annotations

import hashlib
import secrets
import uuid


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_token_id() -> uuid.UUID:
    return uuid.uuid4()


def extract_ip_address(
    forwarded: str | None,
    real_ip: str | None,
    remote_addr: str | None,
) -> str | None:
    if forwarded:
        return forwarded.split(",")[0].strip()
    if real_ip:
        return real_ip
    return remote_addr

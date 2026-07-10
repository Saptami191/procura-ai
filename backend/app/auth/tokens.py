from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    sub: str
    jti: str
    iat: datetime
    exp: datetime
    type: str = "access"


class AccessToken(BaseModel):
    token: str
    expires_at: datetime
    token_type: str = "bearer"


class RefreshToken(BaseModel):
    token: str
    expires_at: datetime
    token_type: str = "bearer"


class TokenPair(BaseModel):
    access_token: AccessToken
    refresh_token: RefreshToken


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="TTL in seconds")

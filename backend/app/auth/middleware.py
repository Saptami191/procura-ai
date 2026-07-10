from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth.jwt import decode_token


class AuthContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        request.state.user_id = None
        request.state.is_authenticated = False

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")
            try:
                payload = decode_token(token)
                sub = payload.get("sub")
                if sub:
                    request.state.user_id = uuid.UUID(sub)
                    request.state.is_authenticated = True
            except Exception:
                pass

        response: Response = await call_next(request)

        if request.state.is_authenticated:
            response.headers["X-User-ID"] = str(request.state.user_id)

        return response

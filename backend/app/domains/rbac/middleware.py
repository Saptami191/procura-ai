from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Thread-safe context storage for membership ID
# In production, this would be replaced with Redis or a proper context manager
MEMBERSHIP_ID_CONTEXT: dict[str, uuid.UUID | None] = {"current": None}


class AuthorizationContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that resolves and caches the user's active membership context.

    Responsibilities:
      1. Extract X-Organization-ID header from request
      2. Resolve the user's active membership for that organization
      3. Store the membership_id in context for downstream dependencies
      4. Future: preload permission cache into request state

    How it integrates:
      - Runs AFTER AuthContextMiddleware (authentication)
      - Runs BEFORE all permission-checking dependencies
      - Sets the membership_id for the current request

    Future enhancements:
      - Load all permissions for the membership into Redis cache
      - Preload ABAC context (time, location, device)
      - Audit log every authorization decision
      - Rate limiting based on permission level
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Reset context for each request
        MEMBERSHIP_ID_CONTEXT["current"] = None

        # Extract organization ID from header (if present)
        org_id_str = request.headers.get("X-Organization-ID")
        if org_id_str:
            try:
                org_id = uuid.UUID(org_id_str)
                # Future: resolve membership from token user_id + org_id
                # For now, the permission dependencies resolve membership directly
                request.state.organization_id = org_id
            except ValueError:
                pass

        response = await call_next(request)
        return response

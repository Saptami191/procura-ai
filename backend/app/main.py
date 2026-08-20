from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from loguru import logger

from app.auth.middleware import AuthContextMiddleware
from app.auth.router import router as auth_router
from app.core import settings, setup_logging
from app.core.exception_handlers import register_exception_handlers
from app.core.health import readiness_status
from app.db import close_db, init_db
from app.domains.organization_membership.router import router as membership_router
from app.domains.rbac.middleware import AuthorizationContextMiddleware
from app.domains.rbac.router import router as rbac_router
from app.domains.user.router import router as users_router
from app.modules.organization.router import router as organization_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Application starting", environment=settings.app_env)
    if settings.database_url:
        await init_db()
    yield
    if settings.database_url:
        await close_db()
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.app_name,
    description="Enterprise AI Workforce Platform - API",
    version=settings.app_version,
    docs_url=settings.api_prefix + "/docs" if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(AuthContextMiddleware)
app.add_middleware(AuthorizationContextMiddleware)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(users_router, prefix=settings.api_prefix)
app.include_router(organization_router, prefix=settings.api_prefix)
app.include_router(membership_router, prefix=settings.api_prefix)
app.include_router(rbac_router, prefix=settings.api_prefix)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} - Enterprise AI Workforce Platform"}


@app.get("/health/live", include_in_schema=False)
async def liveness() -> dict[str, str]:
    """Process-level liveness probe; does not depend on external services."""
    return {"status": "alive"}


@app.get("/health/ready", include_in_schema=False)
async def readiness(response: Response) -> dict[str, object]:
    """Dependency readiness probe for load balancers and orchestrators."""
    result = await readiness_status()
    if result["status"] != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result


@app.get("/health", include_in_schema=False)
async def health(response: Response) -> dict[str, object]:
    """Backward-compatible health endpoint with readiness semantics."""
    result = await readiness_status()
    if result["status"] != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result

from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.core import settings, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Application starting", environment=settings.app_env)
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.app_name,
    description="Enterprise AI Workforce Platform - API",
    version=settings.app_version,
    docs_url=settings.api_prefix + "/docs" if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    lifespan=lifespan,
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Procura AI - Enterprise AI Workforce Platform"}


@app.get("/health")
async def health() -> dict[str, str]:
    logger.debug("Health check called")
    return {"status": "healthy"}

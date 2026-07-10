from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from app.core import settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_db() first.")
    return _engine


def _create_engine() -> AsyncEngine:
    url = settings.database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")

    if settings.is_test:
        return create_async_engine(url, poolclass=NullPool, echo=False)

    return create_async_engine(
        url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=settings.db_pool_pre_ping,
        echo=settings.db_echo and settings.is_development,
        future=True,
    )


async def init_db() -> None:
    global _engine
    if _engine is not None:
        return

    logger.info("Initializing database engine", url=settings.database_url)
    _engine = _create_engine()

    async with _engine.connect() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("SELECT 1")
        )
    logger.info("Database connection established")


async def close_db() -> None:
    global _engine
    if _engine is None:
        return

    logger.info("Closing database engine")
    await _engine.dispose()
    _engine = None
    logger.info("Database engine disposed")

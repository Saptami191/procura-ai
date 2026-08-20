from __future__ import annotations

from typing import Any

from redis.asyncio import Redis
from sqlalchemy import text

from app.core import settings
from app.db.database import get_engine


async def check_database() -> dict[str, Any]:
    """Check that PostgreSQL accepts a lightweight query."""
    try:
        engine = get_engine()
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "error": type(exc).__name__}


async def check_redis() -> dict[str, Any]:
    """Check that Redis accepts a PING without leaking connection details."""
    if not settings.redis_url:
        return {"status": "not_configured"}

    client: Redis | None = None
    try:
        client = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
            health_check_interval=30,
        )
        await client.ping()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "error": type(exc).__name__}
    finally:
        if client is not None:
            await client.aclose()


async def readiness_status() -> dict[str, Any]:
    """Return dependency status for load-balancer/readiness probes."""
    database = await check_database()
    redis = await check_redis()
    dependencies = {"database": database, "redis": redis}
    ready = all(
        dependency["status"] == "ok"
        for dependency in dependencies.values()
    )
    return {
        "status": "ready" if ready else "not_ready",
        "dependencies": dependencies,
    }

from __future__ import annotations

import time
from dataclasses import dataclass

from sqlalchemy import text

from app.db.database import get_engine


@dataclass
class DatabaseHealth:
    status: str = "unhealthy"
    latency_ms: float = 0.0
    pool_size: int = 0
    checked_in: int = 0
    checked_out: int = 0
    overflow: int = 0
    detail: str = ""


async def check_database_health() -> DatabaseHealth:
    health = DatabaseHealth()
    engine = get_engine()

    try:
        start = time.monotonic()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health.latency_ms = round((time.monotonic() - start) * 1000, 2)

        pool = engine.pool
        if pool is not None:
            health.pool_size = pool.size()
            health.checked_in = pool.checkedin()
            health.checked_out = pool.checkedout()
            health.overflow = pool.overflow()

        health.status = "healthy"
    except Exception as exc:
        health.status = "unhealthy"
        health.detail = str(exc)

    return health

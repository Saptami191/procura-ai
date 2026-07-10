from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.exceptions import TransactionError


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> UnitOfWork:
        self.session = self._session_factory()
        self._transaction_nesting = 0
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if self.session is None:
            return

        try:
            if exc_type is not None:
                await self.session.rollback()
                logger.debug("Transaction rolled back due to exception")
            else:
                await self.session.commit()
                logger.debug("Transaction committed")
        except Exception as e:
            await self.session.rollback()
            logger.error("Transaction failed and was rolled back: {}", str(e))
            raise TransactionError(str(e)) from e
        finally:
            await self.session.close()
            self.session = None

    async def commit(self) -> None:
        if self.session is None:
            raise TransactionError("No active session to commit")
        try:
            await self.session.commit()
            logger.debug("Transaction committed")
        except Exception as e:
            await self.session.rollback()
            logger.error("Commit failed, rolled back: {}", str(e))
            raise TransactionError(str(e)) from e

    async def rollback(self) -> None:
        if self.session is None:
            return
        try:
            await self.session.rollback()
            logger.debug("Transaction rolled back")
        except Exception as e:
            logger.error("Rollback failed: {}", str(e))
            raise TransactionError(str(e)) from e

    async def flush(self) -> None:
        if self.session is None:
            raise TransactionError("No active session to flush")
        await self.session.flush()

    @property
    def is_active(self) -> bool:
        return self.session is not None and self.session.is_active


async def unit_of_work(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[UnitOfWork, None]:
    async with UnitOfWork(session_factory) as uow:
        yield uow

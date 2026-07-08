from __future__ import annotations

import logging
import sys

from loguru import logger

from app.core.config import settings
from app.core.constants import Logging as LoggingConstants


class InterceptHandler(logging.Handler):
    """Redirects stdlib logging to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    logger.remove()

    if settings.is_production:
        console_format = LoggingConstants.JSON_FORMAT
        console_level = "WARNING"
    else:
        console_format = LoggingConstants.DEFAULT_FORMAT
        console_level = settings.log_level.upper()

    logger.add(
        sys.stdout,
        format=console_format,
        level=console_level,
        colorize=not settings.is_production,
    )

    logger.add(
        str(settings.log_dir / "procura_{time:YYYY-MM-DD}.log"),
        format=LoggingConstants.JSON_FORMAT,
        level="DEBUG",
        rotation=LoggingConstants.FILE_ROTATION,
        retention=LoggingConstants.FILE_RETENTION,
        compression=LoggingConstants.FILE_COMPRESSION,
        backtrace=True,
        diagnose=settings.is_development,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.DEBUG, force=True)

    logger.info(
        "Logging initialized",
        environment=settings.app_env,
        log_level=console_level,
        log_dir=str(settings.log_dir),
    )

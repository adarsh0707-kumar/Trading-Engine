"""Operational logging configuration for the analytics service."""

from __future__ import annotations

import logging
import os


DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_LOG_FORMAT = (
    "%(asctime)s %(levelname)s %(name)s "
    "[%(threadName)s] %(message)s"
)


class LoggingConfigurationError(ValueError):
    """Raised when logging configuration is invalid."""


def get_configured_log_level(level: str | None = None) -> int:
    """Return the numeric logging level without changing configuration."""

    configured_level = (
        level
        if level is not None
        else os.getenv("TRADING_ENGINE_LOG_LEVEL", DEFAULT_LOG_LEVEL)
    )

    normalized_level = configured_level.strip().upper()

    if not normalized_level:
        raise LoggingConfigurationError(
            "logging level must not be empty"
        )

    numeric_level = getattr(logging, normalized_level, None)

    if not isinstance(numeric_level, int):
        raise LoggingConfigurationError(
            f"unsupported logging level: {configured_level!r}"
        )

    return numeric_level


def configure_logging(
    *,
    level: str | None = None,
    log_format: str | None = None,
) -> None:
    """Configure application-wide operational logging."""

    configured_format = (
        log_format
        if log_format is not None
        else os.getenv("TRADING_ENGINE_LOG_FORMAT", DEFAULT_LOG_FORMAT)
    )

    if not configured_format:
        raise LoggingConfigurationError(
            "logging format must not be empty"
        )

    numeric_level = get_configured_log_level(level)

    logging.basicConfig(
        level=numeric_level,
        format=configured_format,
        force=True,
    )


__all__ = [
    "DEFAULT_LOG_FORMAT",
    "DEFAULT_LOG_LEVEL",
    "LoggingConfigurationError",
    "configure_logging",
    "get_configured_log_level",
]

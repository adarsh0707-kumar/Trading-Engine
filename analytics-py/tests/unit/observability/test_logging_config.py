"""Tests for operational logging configuration."""

from __future__ import annotations

import logging

import pytest

from analytics.observability.logging_config import (
    DEFAULT_LOG_FORMAT,
    DEFAULT_LOG_LEVEL,
    LoggingConfigurationError,
    configure_logging,
    get_configured_log_level,
)


def test_default_log_configuration() -> None:
    """Default configuration should use INFO and the standard format."""

    assert DEFAULT_LOG_LEVEL == "INFO"
    assert "%(levelname)s" in DEFAULT_LOG_FORMAT
    assert "%(message)s" in DEFAULT_LOG_FORMAT


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
    ],
)
def test_get_configured_log_level(
    level: str,
    expected: int,
) -> None:
    """Supported logging levels should map to Python logging values."""

    assert get_configured_log_level(level) == expected


def test_log_level_is_case_insensitive() -> None:
    """Logging levels should accept normal case variations."""

    assert get_configured_log_level("debug") == logging.DEBUG
    assert get_configured_log_level(" Warning ") == logging.WARNING


def test_empty_log_level_is_rejected() -> None:
    """An empty logging level should fail validation."""

    with pytest.raises(
        LoggingConfigurationError,
        match="logging level must not be empty",
    ):
        get_configured_log_level("   ")


def test_unknown_log_level_is_rejected() -> None:
    """Unknown logging levels should fail validation."""

    with pytest.raises(
        LoggingConfigurationError,
        match="unsupported logging level",
    ):
        get_configured_log_level("NOT_A_LEVEL")


def test_configure_logging_sets_root_level() -> None:
    """Logging configuration should update the root logger level."""

    configure_logging(
        level="DEBUG",
        log_format="%(levelname)s %(message)s",
    )

    assert logging.getLogger().level == logging.DEBUG


def test_empty_log_format_is_rejected() -> None:
    """An empty logging format should fail validation."""

    with pytest.raises(
        LoggingConfigurationError,
        match="logging format must not be empty",
    ):
        configure_logging(level="INFO", log_format="")


def test_environment_log_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment configuration should control the default level."""

    monkeypatch.setenv("TRADING_ENGINE_LOG_LEVEL", "DEBUG")

    assert get_configured_log_level() == logging.DEBUG

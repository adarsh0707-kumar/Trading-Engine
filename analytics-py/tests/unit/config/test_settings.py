"""Tests for analytics runtime settings."""

from __future__ import annotations

import math

from analytics.config import ConfigurationError, Settings


def test_settings_default_database_url_is_none() -> None:
    """Database persistence is opt-in by default."""

    settings = Settings()

    assert settings.database_url is None


def test_settings_reads_database_url_from_environment(
    monkeypatch,
) -> None:
    """Settings reads the PostgreSQL URL from the environment."""

    database_url = (
        "postgresql://trading_engine:trading_engine"
        "@127.0.0.1:5432/trading_engine_test"
    )

    monkeypatch.setenv(
        "TRADING_ENGINE_DATABASE_URL",
        database_url,
    )

    settings = Settings.from_environment()

    assert settings.database_url == database_url


def test_settings_reads_none_when_database_url_is_unset(
    monkeypatch,
) -> None:
    """Settings leaves the database URL unset when not configured."""

    monkeypatch.delenv(
        "TRADING_ENGINE_DATABASE_URL",
        raising=False,
    )

    settings = Settings.from_environment()

    assert settings.database_url is None

def test_metrics_configuration_defaults_to_disabled(monkeypatch):
    monkeypatch.delenv("TRADING_ENGINE_METRICS_PORT", raising=False)

    settings = Settings.from_environment()

    assert settings.metrics_port is None
    assert settings.metrics_host == "0.0.0.0"


def test_metrics_configuration_reads_environment(monkeypatch):
    monkeypatch.setenv("TRADING_ENGINE_METRICS_HOST", "127.0.0.1")
    monkeypatch.setenv("TRADING_ENGINE_METRICS_PORT", "9101")

    settings = Settings.from_environment()

    assert settings.metrics_host == "127.0.0.1"
    assert settings.metrics_port == 9101



@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("engine_host", "   ", "engine_host must not be empty"),
        ("engine_port", 0, "engine_port must be between 1 and 65535"),
        ("engine_port", 65536, "engine_port must be between 1 and 65535"),
        ("engine_port", True, "engine_port must be an integer between 1 and 65535"),
        ("connect_timeout", 0, "connect_timeout must be a finite number greater than 0"),
        ("receive_timeout", -1, "receive_timeout must be a finite number greater than 0"),
        ("connect_timeout", math.inf, "connect_timeout must be a finite number greater than 0"),
        ("reconnect_delay", -0.1, "reconnect_delay must be a finite number greater than or equal to 0"),
        ("reconnect_delay", math.inf, "reconnect_delay must be a finite number greater than or equal to 0"),
        ("max_payload_size", 0, "max_payload_size must be greater than 0"),
        ("database_url", "   ", "database_url must not be empty when provided"),
        ("metrics_host", " ", "metrics_host must not be empty"),
        ("metrics_port", 0, "metrics_port must be between 1 and 65535"),
        ("metrics_port", 65536, "metrics_port must be between 1 and 65535"),
    ],
)
def test_settings_rejects_invalid_values(field, value, message):
    with pytest.raises(ConfigurationError, match=message):
        Settings(**{field: value})


def test_settings_accepts_valid_boundary_values():
    settings = Settings(
        engine_port=1,
        connect_timeout=0.0001,
        receive_timeout=0.0001,
        reconnect_delay=0,
        max_payload_size=1,
        metrics_port=65535,
    )

    assert settings.engine_port == 1
    assert settings.connect_timeout == 0.0001
    assert settings.receive_timeout == 0.0001
    assert settings.reconnect_delay == 0
    assert settings.max_payload_size == 1
    assert settings.metrics_port == 65535

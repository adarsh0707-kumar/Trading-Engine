"""Tests for analytics runtime settings."""

from __future__ import annotations

from analytics.config import Settings


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
"""Tests for PostgreSQL health checks."""

from __future__ import annotations

from unittest.mock import MagicMock

from analytics.observability import check_postgres_health


def test_postgres_health_returns_true_for_successful_query() -> None:
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (1,)

    assert check_postgres_health(connection) is True

    cursor.execute.assert_called_once_with("SELECT 1")
    cursor.fetchone.assert_called_once_with()


def test_postgres_health_returns_false_for_unexpected_result() -> None:
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (2,)

    assert check_postgres_health(connection) is False


def test_postgres_health_returns_false_when_query_fails() -> None:
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = RuntimeError("database unavailable")

    assert check_postgres_health(connection) is False


def test_postgres_health_returns_false_when_cursor_creation_fails() -> None:
    connection = MagicMock()
    connection.cursor.side_effect = RuntimeError("connection unavailable")

    assert check_postgres_health(connection) is False

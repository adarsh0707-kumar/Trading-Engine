"""Unit tests for the PostgreSQL connection factory."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from analytics.persistence.postgres.connection import (
    create_postgres_connection,
)


def test_create_postgres_connection_calls_psycopg() -> None:
    """The connection factory delegates to psycopg.connect."""

    database_url = (
        "postgresql://trading_engine:trading_engine"
        "@127.0.0.1:5432/trading_engine_test"
    )

    connection = object()

    with patch(
        "analytics.persistence.postgres.connection.psycopg.connect",
        return_value=connection,
    ) as connect:
        result = create_postgres_connection(database_url)

    assert result is connection
    connect.assert_called_once_with(database_url)


@pytest.mark.parametrize(
    "database_url",
    [
        "",
        "   ",
        "\t",
        "\n",
    ],
)
def test_create_postgres_connection_rejects_empty_url(
    database_url: str,
) -> None:
    """The connection factory rejects empty database URLs."""

    with pytest.raises(ValueError, match="database_url must not be empty"):
        create_postgres_connection(database_url)


@pytest.mark.parametrize(
    "database_url",
    [
        None,
        123,
        object(),
    ],
)
def test_create_postgres_connection_rejects_non_string_url(
    database_url,
) -> None:
    """The connection factory requires a string database URL."""

    with pytest.raises(TypeError, match="database_url must be a string"):
        create_postgres_connection(database_url)
"""Tests for the PostgreSQL repository factory."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from analytics.persistence.postgres.factory import (
    PostgresRepositories,
    create_postgres_repositories,
)


def test_factory_creates_all_repositories_from_one_connection() -> None:
    connection = Mock()

    with patch(
        "analytics.persistence.postgres.factory.create_postgres_connection",
        return_value=connection,
    ) as create_connection:
        repositories = create_postgres_repositories("postgresql://test")

    create_connection.assert_called_once_with("postgresql://test")

    assert isinstance(repositories, PostgresRepositories)
    assert repositories.connection is connection

    assert repositories.trades._connection is connection
    assert repositories.analytics._connection is connection
    assert repositories.positions._connection is connection
    assert repositories.risk._connection is connection

    connection.close.assert_not_called()


def test_factory_closes_connection() -> None:
    connection = Mock()

    repositories = PostgresRepositories(
        connection=connection,
        trades=Mock(),
        analytics=Mock(),
        positions=Mock(),
        risk=Mock(),
    )

    repositories.close()

    connection.close.assert_called_once_with()


@pytest.mark.parametrize(
    "repository_name",
    [
        "trades",
        "analytics",
        "positions",
        "risk",
    ],
)
def test_factory_exposes_expected_repository(
    repository_name: str,
) -> None:
    connection = Mock()

    with patch(
        "analytics.persistence.postgres.factory.create_postgres_connection",
        return_value=connection,
    ):
        repositories = create_postgres_repositories("postgresql://test")

    repository = getattr(repositories, repository_name)

    assert repository is not None


def test_factory_closes_connection_if_repository_creation_fails() -> None:
    connection = Mock()

    with (
        patch(
            "analytics.persistence.postgres.factory.create_postgres_connection",
            return_value=connection,
        ),
        patch(
            "analytics.persistence.postgres.factory.PostgresRiskRepository",
            side_effect=RuntimeError("repository creation failed"),
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="repository creation failed",
        ):
            create_postgres_repositories("postgresql://test")

    connection.close.assert_called_once_with()
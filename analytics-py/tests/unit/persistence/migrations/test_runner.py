"""Unit tests for the migration runner."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from analytics.persistence.migrations.runner import MigrationRunner


def _write_migration(
    directory: Path,
    filename: str,
    sql: str = "SELECT 1;",
) -> None:
    (directory / filename).write_text(sql, encoding="utf-8")


def _configure_cursor(cursor: MagicMock) -> MagicMock:
    """Make a mocked cursor behave like a Psycopg cursor context manager."""

    cursor.__enter__.return_value = cursor
    cursor.__exit__.return_value = None
    return cursor


def test_discover_orders_migrations_by_numeric_version(tmp_path: Path) -> None:
    _write_migration(tmp_path, "010_second.sql")
    _write_migration(tmp_path, "002_first.sql")
    _write_migration(tmp_path, "001_initial.sql")
    _write_migration(tmp_path, "README.sql")

    migrations = MigrationRunner(MagicMock(), tmp_path).discover()

    assert [migration.version for migration in migrations] == ["001", "002", "010"]


def test_discover_ignores_invalid_filenames(tmp_path: Path) -> None:
    _write_migration(tmp_path, "001_valid.sql")
    _write_migration(tmp_path, "invalid.sql")
    _write_migration(tmp_path, "002-incorrect.sql")
    _write_migration(tmp_path, "003_UPPERCASE.sql")

    migrations = MigrationRunner(MagicMock(), tmp_path).discover()

    assert [migration.version for migration in migrations] == ["001"]


def test_discover_rejects_duplicate_versions(tmp_path: Path) -> None:
    _write_migration(tmp_path, "001_initial.sql")
    _write_migration(tmp_path, "001_second.sql")

    with pytest.raises(ValueError, match="duplicate migration version: 001"):
        MigrationRunner(MagicMock(), tmp_path).discover()


def test_discover_requires_existing_directory(tmp_path: Path) -> None:
    runner = MigrationRunner(MagicMock(), tmp_path / "missing")

    with pytest.raises(FileNotFoundError):
        runner.discover()


def test_runner_rejects_none_connection(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="connection must not be None"):
        MigrationRunner(None, tmp_path)  # type: ignore[arg-type]


def test_run_applies_pending_migrations(tmp_path: Path) -> None:
    _write_migration(tmp_path, "001_initial.sql", "CREATE TABLE example (id INTEGER);")
    _write_migration(tmp_path, "002_second.sql", "ALTER TABLE example ADD COLUMN name TEXT;")

    connection = MagicMock()
    transaction = connection.transaction.return_value
    transaction.__enter__.return_value = transaction

    migration_table_cursor = _configure_cursor(MagicMock())
    migration_table_cursor.fetchall.return_value = []
    migration_cursor = _configure_cursor(MagicMock())

    connection.cursor.side_effect = [
        migration_table_cursor,
        migration_table_cursor,
        migration_cursor,
        migration_cursor,
    ]

    applied = MigrationRunner(connection, tmp_path).run()

    assert applied == ("001", "002")
    assert connection.transaction.call_count == 1
    assert migration_cursor.execute.call_count == 4


def test_run_is_idempotent(tmp_path: Path) -> None:
    _write_migration(tmp_path, "001_initial.sql", "CREATE TABLE example (id INTEGER);")

    connection = MagicMock()
    transaction = connection.transaction.return_value
    transaction.__enter__.return_value = transaction

    migration_table_cursor = _configure_cursor(MagicMock())
    migration_table_cursor.fetchall.return_value = [("001",)]
    connection.cursor.return_value = migration_table_cursor

    applied = MigrationRunner(connection, tmp_path).run()

    assert applied == ()
    assert connection.transaction.call_count == 1
    assert migration_table_cursor.execute.call_count == 2


def test_run_uses_existing_applied_versions(tmp_path: Path) -> None:
    _write_migration(tmp_path, "001_initial.sql")
    _write_migration(tmp_path, "002_second.sql")

    connection = MagicMock()
    transaction = connection.transaction.return_value
    transaction.__enter__.return_value = transaction

    migration_table_cursor = _configure_cursor(MagicMock())
    migration_table_cursor.fetchall.return_value = [("001",)]
    migration_cursor = _configure_cursor(MagicMock())

    connection.cursor.side_effect = [
        migration_table_cursor,
        migration_table_cursor,
        migration_cursor,
    ]

    applied = MigrationRunner(connection, tmp_path).run()

    assert applied == ("002",)
    assert migration_cursor.execute.call_count == 2

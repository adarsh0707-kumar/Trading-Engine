"""Execute versioned PostgreSQL migrations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import psycopg

_MIGRATION_NAME = re.compile(r"^(?P<version>\d+)_[a-z0-9_]+\.sql$")


@dataclass(frozen=True, slots=True)
class Migration:
    """A discovered SQL migration file."""

    version: str
    path: Path


class MigrationRunner:
    """Apply ordered SQL migrations using an existing Psycopg connection."""

    def __init__(
        self,
        connection: psycopg.Connection,
        migrations_path: str | Path,
    ) -> None:
        if connection is None:
            raise TypeError("connection must not be None")

        self._connection = connection
        self._migrations_path = Path(migrations_path)

    def discover(self) -> tuple[Migration, ...]:
        """Discover and validate versioned SQL migration files."""

        if not self._migrations_path.is_dir():
            raise FileNotFoundError(self._migrations_path)

        migrations: list[Migration] = []
        seen_versions: set[str] = set()

        for path in sorted(self._migrations_path.glob("*.sql")):
            match = _MIGRATION_NAME.fullmatch(path.name)
            if match is None:
                continue

            version = match.group("version")

            if version in seen_versions:
                raise ValueError(f"duplicate migration version: {version}")

            seen_versions.add(version)
            migrations.append(
                Migration(
                    version=version,
                    path=path,
                )
            )

        return tuple(
            sorted(
                migrations,
                key=lambda migration: int(migration.version),
            )
        )

    def run(self) -> tuple[str, ...]:
        """Apply all pending migrations atomically.

        The migration table creation, migration SQL, and migration records
        all execute inside one transaction. If any migration fails, the
        entire migration run is rolled back.
        """

        migrations = self.discover()

        with self._connection.transaction():
            self._ensure_migration_table()

            applied = self._applied_versions()
            newly_applied: list[str] = []

            for migration in migrations:
                if migration.version in applied:
                    continue

                sql = migration.path.read_text(encoding="utf-8")

                with self._connection.cursor() as cursor:
                    cursor.execute(sql)
                    cursor.execute(
                        """
                        INSERT INTO schema_migrations (version)
                        VALUES (%s)
                        """,
                        (migration.version,),
                    )

                newly_applied.append(migration.version)

        return tuple(newly_applied)

    def _ensure_migration_table(self) -> None:
        """Create the migration tracking table if necessary."""

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def _applied_versions(self) -> set[str]:
        """Return versions already recorded as applied."""

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT version
                FROM schema_migrations
                """
            )

            return {row[0] for row in cursor.fetchall()}


__all__ = ["Migration", "MigrationRunner"]

import reflex as rx

import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

from app import menu_database as database
from app.models import Base


class ManagedURLTests(unittest.TestCase):
    def test_direct_url_survives_legacy_routing_and_has_priority(self):
        url = database.managed_menu_url(
            {
                "REFLEX_DB_DIRECT_URL": "postgresql://user:secret@example.test/menu",
                "REFLEX_DEV_DB_DIRECT_URL": "postgresql://other:secret@dev.test/menu",
                "REFLEX_DB_URL": "sqlite:///legacy.db",
            }
        )
        self.assertEqual(url.drivername, "postgresql+psycopg")
        self.assertEqual(url.host, "example.test")

    def test_dev_direct_fallback_and_driver_normalization(self):
        for scheme in (
            "postgres",
            "postgresql",
            "postgresql+asyncpg",
            "postgresql+psycopg",
        ):
            with self.subTest(scheme=scheme):
                url = database.managed_menu_url(
                    {
                        "REFLEX_DEV_DB_DIRECT_URL": f"{scheme}://user:secret@dev.test/menu?sslmode=require"
                    }
                )
                self.assertEqual(url.drivername, "postgresql+psycopg")
                self.assertEqual(url.query["sslmode"], "require")

    def test_missing_or_invalid_direct_url_fails_without_legacy_fallback(self):
        for env in (
            {"REFLEX_DB_URL": "postgresql://user:secret@legacy.test/menu"},
            {"REFLEX_DB_DIRECT_URL": "sqlite:///test.db"},
            {"REFLEX_DB_DIRECT_URL": "invalid-secret-value"},
        ):
            with self.subTest(env_keys=list(env)):
                with self.assertRaises(RuntimeError) as error:
                    database.managed_menu_url(env)
                self.assertNotIn("secret", str(error.exception))


class BootstrapScopeTests(unittest.TestCase):
    def test_metadata_copies_only_three_existing_tables(self):
        metadata = database.menu_metadata()
        self.assertIsNot(metadata, Base.metadata)
        self.assertEqual(
            set(metadata.tables),
            {"menu_auth_account", "menu_auth_session", "menu_setting"},
        )
        for table in metadata.tables.values():
            self.assertIsNot(table, Base.metadata.tables[table.name])
            for foreign_key in table.foreign_keys:
                self.assertEqual(
                    foreign_key.column.table.name, "menu_auth_account"
                )
            ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
            self.assertNotIn("farm_team", ddl)

    def test_bootstrap_locks_before_scoped_ddl_and_import(self):
        url = database.managed_menu_url(
            {"REFLEX_DB_DIRECT_URL": "postgresql://user:secret@db.test/menu"}
        )
        engine = MagicMock()
        connection = engine.begin.return_value.__enter__.return_value
        metadata = database.menu_metadata()
        events = []
        connection.execute.side_effect = lambda *args, **kwargs: events.append(
            "lock"
        )
        with (
            patch.object(database, "create_engine", return_value=engine),
            patch.object(database, "menu_metadata", return_value=metadata),
            patch.object(
                metadata,
                "create_all",
                side_effect=lambda *args, **kwargs: events.append("ddl"),
            ) as ddl,
            patch.object(
                database,
                "import_local_menu_data",
                side_effect=lambda *args: events.append("import"),
            ),
        ):
            database._bootstrap_menu_database.__wrapped__(url, True)
        self.assertEqual(events, ["lock", "ddl", "import"])
        ddl.assert_called_once_with(connection, checkfirst=True)
        sql, parameters = connection.execute.call_args.args
        self.assertIn("pg_advisory_xact_lock", str(sql))
        self.assertEqual(parameters["key"], database.MENU_LOCK_ID)
        engine.dispose.assert_called_once()

    def test_bootstrap_failure_is_not_cached_or_reported_as_success(self):
        database._bootstrap_menu_database.cache_clear()
        url = database.managed_menu_url(
            {"REFLEX_DB_DIRECT_URL": "postgresql://user:secret@db.test/menu"}
        )
        engine = MagicMock()
        engine.begin.side_effect = RuntimeError("unavailable")
        with (
            patch.object(database, "create_engine", return_value=engine),
            patch("logging.exception"),
        ):
            for _ in range(2):
                with self.assertRaises(RuntimeError):
                    database._bootstrap_menu_database(url, True)
        self.assertEqual(engine.begin.call_count, 2)
        database._bootstrap_menu_database.cache_clear()


class AtomicImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "source.db"
        self.source = create_engine(f"sqlite:///{self.path}")
        self.destination = create_engine(
            f"sqlite:///{self.temp.name}/destination.db"
        )
        self.metadata = database.menu_metadata()
        self.metadata.create_all(self.source)
        self.metadata.create_all(self.destination)
        self.now = dt.datetime.now(dt.UTC)
        self.password_hash = f"pbkdf2_sha256$600000${'ab' * 32}${'cd' * 32}"
        with self.source.begin() as connection:
            connection.execute(
                self.metadata.tables["menu_auth_account"].insert(),
                {
                    "id": 42,
                    "email": "admin@example.test",
                    "password_hash": self.password_hash,
                    "is_admin": True,
                    "created_at": self.now,
                },
            )
            connection.execute(
                self.metadata.tables["menu_auth_session"].insert(),
                {
                    "account_id": 42,
                    "token_hash": "ef" * 32,
                    "expires_at": self.now + dt.timedelta(days=7),
                    "created_at": self.now,
                    "is_revoked": False,
                },
            )
            connection.execute(
                self.metadata.tables["menu_setting"].insert(),
                {
                    "navigation_key": "agricole",
                    "enabled": False,
                    "updated_by_account_id": 42,
                    "updated_at": self.now,
                },
            )

    def tearDown(self):
        self.source.dispose()
        self.destination.dispose()
        self.temp.cleanup()

    def test_atomic_import_maps_ids_preserves_hashes_and_never_overwrites(self):
        with self.destination.begin() as connection:
            database.import_local_menu_data(
                connection, self.metadata, self.path
            )
        with self.destination.begin() as connection:
            account = (
                connection.execute(
                    select(self.metadata.tables["menu_auth_account"])
                )
                .mappings()
                .one()
            )
            session = (
                connection.execute(
                    select(self.metadata.tables["menu_auth_session"])
                )
                .mappings()
                .one()
            )
            setting = (
                connection.execute(select(self.metadata.tables["menu_setting"]))
                .mappings()
                .one()
            )
            self.assertEqual(account["password_hash"], self.password_hash)
            self.assertTrue(account["is_admin"])
            self.assertEqual(session["token_hash"], "ef" * 32)
            self.assertEqual(session["account_id"], account["id"])
            self.assertEqual(setting["updated_by_account_id"], account["id"])
            self.assertFalse(setting["enabled"])
            connection.execute(text("UPDATE menu_setting SET enabled = TRUE"))
        with self.destination.begin() as connection:
            with patch.object(
                database,
                "_local_menu_snapshot",
                side_effect=AssertionError("stale source read"),
            ):
                database.import_local_menu_data(
                    connection, self.metadata, self.path
                )
            self.assertTrue(
                connection.execute(
                    select(self.metadata.tables["menu_setting"].c.enabled)
                ).scalar_one()
            )
        self.assertEqual(
            set(inspect(self.destination).get_table_names()),
            set(self.metadata.tables),
        )

    def test_failed_import_rolls_back_all_identities_and_retry_is_possible(
        self,
    ):
        with self.source.begin() as connection:
            connection.execute(
                text("UPDATE menu_auth_session SET token_hash = 'invalid'")
            )
        with self.assertRaises(RuntimeError):
            with self.destination.begin() as connection:
                database.import_local_menu_data(
                    connection, self.metadata, self.path
                )
        with self.destination.connect() as connection:
            for table in self.metadata.tables.values():
                self.assertIsNone(
                    connection.execute(select(table.c.id)).first()
                )
        with self.source.begin() as connection:
            connection.execute(
                text("UPDATE menu_auth_session SET token_hash = :hash"),
                {"hash": "ef" * 32},
            )
        with self.destination.begin() as connection:
            database.import_local_menu_data(
                connection, self.metadata, self.path
            )
            self.assertIsNotNone(
                connection.execute(
                    select(self.metadata.tables["menu_auth_account"].c.id)
                ).first()
            )


if __name__ == "__main__":
    unittest.main()

import reflex as rx

import tempfile
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import menu_service
from app.menu_policy import (
    ENTRY_MODULES,
    GLOBAL_KEYS,
    PERMISSIONS,
    evaluate_policy,
    read_local_rights,
    resolve_policy,
    validate_policy_key,
)
from app.menu_database import menu_metadata
from app.navigation import NAVIGATION


OWNER = {"id": 1, "email": "owner@example.test", "admin": True}
READER = {"id": 2, "email": "reader@example.test", "admin": False}


class PolicyTests(unittest.TestCase):
    def test_anonymous_and_unassigned_accounts_have_nothing(self):
        for account in ({"id": 0, "email": "", "admin": False}, READER):
            policy = evaluate_policy(account, {}, first_account_id=1)
            self.assertEqual(policy["permissions"], [])
            self.assertEqual(policy["navigation"], [])
            self.assertEqual(policy["cockpits"], [])
            self.assertFalse(policy["admin"])

    def test_only_first_existing_admin_bootstraps_owner(self):
        policy = evaluate_policy(OWNER, {}, first_account_id=1)
        self.assertEqual(policy["roles"], ["proprietaire"])
        self.assertEqual(set(policy["permissions"]), PERMISSIONS)
        self.assertTrue(policy["admin"])
        unrelated = evaluate_policy(
            {**READER, "admin": True}, {}, first_account_id=1
        )
        self.assertEqual(unrelated["permissions"], [])

    def test_multiple_roles_union_and_deny_wins(self):
        rows = {
            "policy:account:2:role:responsable-stock": True,
            "policy:account:2:role:responsable-materiel": True,
        }
        policy = evaluate_policy(READER, rows)
        self.assertIn("stocks:CONSULTER", policy["permissions"])
        self.assertIn("materiel:CONSULTER", policy["permissions"])
        rows.update(
            {
                "policy:role:responsable-stock:permission:stocks:CONSULTER": False,
                "policy:account:2:permission:stocks:CONSULTER": True,
                "policy:account:2:permission:materiel:CONSULTER": False,
            }
        )
        policy = evaluate_policy(READER, rows)
        self.assertNotIn("stocks:CONSULTER", policy["permissions"])
        self.assertNotIn("materiel:CONSULTER", policy["permissions"])
        self.assertIn("maintenance:CONSULTER", policy["permissions"])

    def test_account_grants_without_role_and_status(self):
        rows = {"policy:account:2:permission:stocks:CONSULTER": True}
        self.assertEqual(
            evaluate_policy(READER, rows)["navigation"][0]["key"],
            "stocks.magasin",
        )
        rows["policy:account:2:active"] = False
        self.assertEqual(evaluate_policy(READER, rows)["navigation"], [])

    def test_disabled_parent_child_and_empty_groups(self):
        rows = {
            "agricole": False,
            "stocks.magasin": False,
            "configuration": False,
        }
        policy = evaluate_policy(OWNER, rows, first_account_id=1)
        parents = {item["key"] for item in policy["cockpits"]}
        self.assertNotIn("agricole", parents)
        self.assertNotIn("stocks", parents)
        self.assertNotIn("configuration", parents)
        self.assertNotIn("elevage", parents)
        self.assertNotIn("infrastructures", parents)
        self.assertEqual(
            parents, {entry["cockpit"] for entry in policy["navigation"]}
        )

    def test_registry_validation_and_complete_mapping(self):
        self.assertEqual(
            set(ENTRY_MODULES), {entry["key"] for entry in NAVIGATION}
        )
        for key in (
            "policy:account:2:active",
            "policy:account:2:role:consultation",
            "policy:role:comptable:permission:ventes:CONSULTER",
        ):
            self.assertTrue(validate_policy_key(key))
        for key in (
            "policy:account:02:active",
            "policy:account:0:active",
            "policy:account:2:role:invented",
            "policy:role:comptable:permission:invented:CONSULTER",
            "policy:account:2:permission:stocks:INVENTED",
        ):
            self.assertFalse(validate_policy_key(key))

    def test_crm_tabs_and_duplicate_routes_are_independent(self):
        policy = evaluate_policy(
            READER, {"policy:account:2:permission:ventes:CONSULTER": True}
        )
        keys = {entry["key"] for entry in policy["navigation"]}
        self.assertIn("commercial.clients", keys)
        self.assertIn("partenaires.clients", keys)
        self.assertNotIn("achats.fournisseurs", keys)
        self.assertNotIn("commercial.overview", keys)
        self.assertEqual(set(policy["crm_tabs"]), {"clients", "ventes"})

    def test_unique_normalized_local_match_and_inactive_status(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "local.db"
            with sqlite3.connect(path) as connection:
                connection.executescript("""
                    CREATE TABLE app_user (id INTEGER, email TEXT, status TEXT);
                    CREATE TABLE app_role (id INTEGER, key TEXT, is_active BOOLEAN);
                    CREATE TABLE user_role (user_id INTEGER, role_id INTEGER);
                    CREATE TABLE app_permission (id INTEGER, key TEXT);
                    CREATE TABLE role_permission (role_id INTEGER, permission_id INTEGER, is_granted BOOLEAN);
                    INSERT INTO app_user VALUES (90, ' READER@example.test ', 'ACTIF');
                    INSERT INTO app_role VALUES (7, 'consultation', TRUE);
                    INSERT INTO user_role VALUES (90, 7);
                    INSERT INTO app_permission VALUES (4, 'parcelles:CONSULTER');
                    INSERT INTO role_permission VALUES (7, 4, FALSE);
                """)
            local = read_local_rights(READER["email"], path)
            policy = evaluate_policy(READER, {}, local=local)
            self.assertEqual(policy["roles"], ["consultation"])
            self.assertNotIn("parcelles:CONSULTER", policy["permissions"])
            self.assertEqual(
                read_local_rights("unrelated@example.test", path)["roles"], []
            )
            with sqlite3.connect(path) as connection:
                connection.execute("UPDATE app_user SET status='SUSPENDU'")
            self.assertEqual(
                evaluate_policy(
                    READER, {}, local=read_local_rights(READER["email"], path)
                )["navigation"],
                [],
            )
            with sqlite3.connect(path) as connection:
                connection.execute(
                    "INSERT INTO app_user VALUES (91, 'reader@example.test', 'ACTIF')"
                )
            self.assertEqual(
                read_local_rights(READER["email"], path)["roles"], []
            )

    def test_missing_local_database_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.db"
            rights = read_local_rights(READER["email"], path)
            self.assertEqual(rights["roles"], [])
            self.assertFalse(path.exists())


class FreshResolveTests(unittest.IsolatedAsyncioTestCase):
    async def test_fresh_resolve_sees_changes_and_read_settings_excludes_policy(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_async_engine(
                f"sqlite+aiosqlite:///{directory}/policy.db"
            )
            factory = async_sessionmaker(engine)
            try:
                async with engine.begin() as connection:
                    await connection.run_sync(menu_metadata().create_all)
                with (
                    patch.object(menu_service, "menu_session", factory),
                    patch.object(
                        menu_service, "ensure_menu_database", AsyncMock()
                    ),
                    patch(
                        "app.menu_policy.read_local_rights",
                        return_value={
                            "active": True,
                            "roles": [],
                            "overrides": {},
                        },
                    ),
                ):
                    _, owner = await menu_service.authenticate(
                        "owner@example.test", "isolated-owner-password", True
                    )
                    token, reader = await menu_service.authenticate(
                        "reader@example.test", "isolated-reader-password", True
                    )
                    self.assertFalse(reader["admin"])
                    self.assertEqual(
                        (await resolve_policy(token))["navigation"], []
                    )
                    async with factory() as session:
                        await session.execute(
                            text(
                                "INSERT INTO menu_setting (navigation_key, enabled, updated_at, updated_by_account_id) VALUES (:key, TRUE, CURRENT_TIMESTAMP, :owner)"
                            ),
                            {
                                "key": f"policy:account:{reader['id']}:role:consultation",
                                "owner": owner["id"],
                            },
                        )
                        await session.commit()
                    fresh = await resolve_policy(token)
                    self.assertIn("parcelles:CONSULTER", fresh["permissions"])
                    self.assertEqual(await menu_service.read_settings(), {})
                    async with factory() as session:
                        await session.execute(
                            text("UPDATE menu_setting SET enabled=FALSE")
                        )
                        await session.commit()
                    self.assertEqual(
                        (await resolve_policy(token))["navigation"], []
                    )
                    self.assertTrue(set(fresh["settings"]) <= GLOBAL_KEYS)
            finally:
                await engine.dispose()

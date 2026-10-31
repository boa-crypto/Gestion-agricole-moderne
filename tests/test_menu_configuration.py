import reflex as rx

import asyncio
import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import menu_service as service
from app.models import MenuAuthAccount, MenuAuthSession, MenuSetting
from app.navigation import COCKPITS, NAVIGATION
from app.states.navigation_state import NavigationState
from app.menu_policy import evaluate_policy


class CatalogTests(unittest.TestCase):
    def test_catalog_covers_every_available_parent_and_child(self):
        rows = service.menu_catalog({})
        keys = {row["key"] for row in rows}
        expected = {c["key"] for c in COCKPITS if c["available"]} | {
            e["key"] for e in NAVIGATION
        }
        self.assertEqual(keys, expected)
        self.assertEqual(len(rows), len(keys))
        self.assertTrue(all(row["effective"] for row in rows))

    def test_parent_restores_individual_child_flags(self):
        settings = {"agricole": False, "agricole.parcelles": False}
        rows = {row["key"]: row for row in service.menu_catalog(settings)}
        self.assertTrue(rows["agricole.referentiel"]["enabled"])
        self.assertFalse(rows["agricole.referentiel"]["effective"])
        settings["agricole"] = True
        restored = {row["key"]: row for row in service.menu_catalog(settings)}
        self.assertTrue(restored["agricole.referentiel"]["effective"])
        self.assertFalse(restored["agricole.parcelles"]["effective"])
        protected = {
            row["key"]: row
            for row in service.menu_catalog(
                {k: False for k in service.PROTECTED_KEYS}
            )
        }
        self.assertTrue(
            all(not protected[k]["effective"] for k in service.PROTECTED_KEYS)
        )

    def test_accent_case_key_and_composed_filters(self):
        rows = service.menu_catalog({"agricole": False})
        self.assertEqual(
            service.filter_catalog(
                rows, "REFERENTIEL", "Désactivés", "Sous-menus"
            )[0]["key"],
            "agricole.referentiel",
        )
        self.assertEqual(
            service.filter_catalog(
                rows, "AGRICOLE.PARCELLES", "Désactivés", "Sous-menus"
            )[0]["key"],
            "agricole.parcelles",
        )
        self.assertEqual(
            service.filter_catalog(rows, "agricole", "Activés", "Principaux"),
            [],
        )
        self.assertEqual(
            service.filter_catalog(rows, "inexistant", "Tous", "Tous"), []
        )

    def test_navigation_filters_every_surface_and_falls_back(self):
        nav = NavigationState()
        nav._apply_policy(
            evaluate_policy(
                {"id": 1, "email": "owner@example.test", "admin": True},
                {"global": False, "agricole": False},
                first_account_id=1,
            )
        )
        self.assertFalse(nav.global_visible)
        self.assertFalse(nav.search_visible)
        self.assertNotIn("global", {c["key"] for c in nav.cockpits})
        self.assertNotIn(
            "agricole", {e["cockpit"] for e in nav.visible_navigation}
        )
        self.assertEqual(nav.current_key, "configuration.menus")
        self.assertEqual(nav.selected_cockpit, "configuration")

    def test_registration_gate_and_accessible_switch(self):
        app = Path("app/app.py").read_text()
        self.assertIn('route="/configuration"', app)
        self.assertIn('NavigationState.enter_page("configuration")', app)
        page = Path("app/pages/configuration.py").read_text()
        self.assertIn("MenuConfigurationState.allowed", page)
        self.assertIn("login_panel()", page)
        self.assertIn('app_shell(', page)
        self.assertIn('"configuration",', page)
        component = Path("app/components/menu_configuration.py").read_text()
        self.assertIn('role="switch"', component)
        self.assertIn('aria_checked=row["enabled"]', component)

    def test_password_salts_and_validation(self):
        password = "une phrase très longue et unique"
        first = service.hash_password(password)
        second = service.hash_password(password)
        self.assertNotEqual(first, second)
        self.assertTrue(service.verify_password(password, first))
        self.assertFalse(service.verify_password("incorrect", first))
        self.assertFalse(service.verify_password(password, "malformed"))


class PersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.temp.name}/test.db"
        )
        # Seulement les trois modèles demandés, dans une base de test isolée.
        async with self.engine.begin() as connection:
            await connection.run_sync(
                lambda conn: MenuAuthAccount.__table__.create(conn)
            )
            await connection.run_sync(
                lambda conn: MenuAuthSession.__table__.create(conn)
            )
            await connection.run_sync(
                lambda conn: MenuSetting.__table__.create(conn)
            )
        self.factory = async_sessionmaker(self.engine)

        async def initialized():
            return

        self.session_patch = patch.object(service, "menu_session", self.factory)
        self.ensure_patch = patch.object(
            service, "ensure_menu_database", initialized
        )
        self.session_patch.start()
        self.ensure_patch.start()

    async def asyncTearDown(self):
        self.session_patch.stop()
        self.ensure_patch.stop()
        await self.engine.dispose()
        self.temp.cleanup()

    async def test_public_settings_and_revocation_use_isolated_database(self):
        self.assertEqual(await service.read_settings("", False), {})
        with self.assertRaises(PermissionError):
            await service.read_settings("", True)
        token, _ = await service.authenticate(
            "navigation@example.com", "long-password-navigation", True
        )
        expected = await service.toggle_setting(token, "agricole.parcelles")
        self.assertEqual(expected, {"agricole.parcelles": False})
        self.assertEqual(await service.read_settings("", False), expected)
        await service.revoke_session(token)
        async with self.factory() as session:
            revoked = (
                await session.execute(
                    text(
                        "SELECT is_revoked FROM menu_auth_session WHERE token_hash = :token"
                    ),
                    {"token": service.token_hash(token)},
                )
            ).scalar_one()
        self.assertTrue(revoked)
        with self.assertRaises(PermissionError):
            await service.resolve_account(token)
        with self.assertRaises(PermissionError):
            await service.read_settings(token, True)
        with self.assertRaises(PermissionError):
            await service.toggle_setting(token, "agricole.parcelles")
        self.assertEqual(await service.read_settings("", False), expected)

    async def test_first_signup_atomic_role_and_persistent_flags(self):
        accounts = await asyncio.gather(
            service.authenticate("one@example.com", "long-password-one", True),
            service.authenticate("two@example.com", "long-password-two", True),
        )
        self.assertEqual(sum(account["admin"] for _, account in accounts), 1)
        admin_token = next(
            token for token, account in accounts if account["admin"]
        )
        viewer_token = next(
            token for token, account in accounts if not account["admin"]
        )
        await service.toggle_setting(admin_token, "agricole.parcelles")
        await service.toggle_setting(admin_token, "agricole")
        loaded = await service.read_settings(admin_token, True)
        self.assertFalse(loaded["agricole.parcelles"])
        self.assertFalse(loaded["agricole"])
        await service.toggle_setting(admin_token, "agricole")
        loaded = await service.read_settings(admin_token, True)
        self.assertTrue(loaded["agricole"])
        self.assertFalse(loaded["agricole.parcelles"])
        with self.assertRaises(PermissionError):
            await service.toggle_setting(viewer_token, "agricole")
        with self.assertRaises(PermissionError):
            await service.read_settings(viewer_token, True)
        with self.assertRaises(PermissionError):
            await service.toggle_setting("fabricated", "agricole")
        for key in service.PROTECTED_KEYS:
            with self.assertRaises(ValueError):
                await service.toggle_setting(admin_token, key)
        self.assertEqual(loaded, await service.read_settings(admin_token, True))

    async def test_session_restore_expiry_revocation_and_db_role(self):
        token, account = await service.authenticate(
            "admin@example.com", "long-password-admin", True
        )
        self.assertEqual(await service.resolve_account(token), account)
        async with self.factory() as session:
            stored = (
                await session.execute(
                    text("SELECT token_hash FROM menu_auth_session")
                )
            ).scalar_one()
            self.assertNotEqual(stored, token)
            await session.execute(
                text("UPDATE menu_auth_account SET is_admin = 0")
            )
            await session.commit()
        with self.assertRaises(PermissionError):
            await service.toggle_setting(token, "global")
        new_token, _ = await service.authenticate(
            "admin@example.com", "long-password-admin", False, token
        )
        with self.assertRaises(PermissionError):
            await service.resolve_account(token)
        await service.revoke_session(new_token)
        with self.assertRaises(PermissionError):
            await service.resolve_account(new_token)
        expiring, _ = await service.authenticate(
            "admin@example.com", "long-password-admin", False
        )
        async with self.factory() as session:
            await session.execute(
                text(
                    "UPDATE menu_auth_session SET expires_at = :past WHERE token_hash = :token"
                ),
                {
                    "past": str(dt.datetime(2000, 1, 1)),
                    "token": service.token_hash(expiring),
                },
            )
            await session.commit()
        with self.assertRaises(PermissionError):
            await service.resolve_account(expiring)

    async def test_reload_keeps_identity_session_and_settings(self):
        token, account = await service.authenticate(
            "reload@example.com", "long-password-reload", True
        )
        await service.toggle_setting(token, "agricole.parcelles")
        await self.engine.dispose()
        replacement = create_async_engine(
            f"sqlite+aiosqlite:///{self.temp.name}/test.db"
        )
        try:
            with patch.object(
                service, "menu_session", async_sessionmaker(replacement)
            ):
                self.assertEqual(await service.resolve_account(token), account)
                self.assertFalse(
                    (await service.read_settings(token, True))[
                        "agricole.parcelles"
                    ]
                )
                _, restored = await service.authenticate(
                    "reload@example.com", "long-password-reload", False
                )
                self.assertEqual(restored, account)
                _, viewer = await service.authenticate(
                    "after@example.com", "long-password-after", True
                )
                self.assertFalse(viewer["admin"])
        finally:
            await replacement.dispose()

    async def test_duplicate_email_and_wrong_password_do_not_elevate(self):
        await service.authenticate(
            "admin@example.com", "long-password-admin", True
        )
        with self.assertRaises(ValueError):
            await service.authenticate(
                " ADMIN@example.com ", "long-password-other", True
            )
        with self.assertRaises(ValueError):
            await service.authenticate(
                "admin@example.com", "incorrect-password", False
            )
        _, viewer = await service.authenticate(
            "viewer@example.com", "long-password-viewer", True
        )
        self.assertFalse(viewer["admin"])


if __name__ == "__main__":
    unittest.main()

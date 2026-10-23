import reflex as rx

import asyncio
import datetime as dt
import inspect
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import menu_service
from app.menu_database import menu_metadata
from app.menu_policy import resolve_policy
from app.menu_policy_admin import (
    ConfigurationDenied,
    SessionExpired,
    audit_key,
    canonical_id,
    edit_policy,
    read_administration,
)
from app.states.menu_configuration_state import MenuConfigurationState
from app.states.navigation_state import NavigationState


class GuardedEditsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.directory.name}/administration.db"
        )
        self.factory = async_sessionmaker(self.engine)
        async with self.engine.begin() as connection:
            await connection.run_sync(menu_metadata().create_all)
        self.patches = [
            patch.object(menu_service, "menu_session", self.factory),
            patch.object(menu_service, "ensure_menu_database", AsyncMock()),
            patch(
                "app.menu_policy.read_local_rights",
                return_value={"active": True, "roles": [], "overrides": {}},
            ),
            patch(
                "app.menu_policy_admin.read_local_rights",
                return_value={"active": True, "roles": [], "overrides": {}},
            ),
            patch(
                "app.menu_policy_admin.local_match",
                return_value="Aucune correspondance locale",
            ),
        ]
        for item in self.patches:
            item.start()
        async with self.factory() as session:
            for number, email, admin, token in [
                (1, "owner@example.test", True, "owner"),
                (2, "member@example.test", False, "member"),
            ]:
                await session.execute(
                    text(
                        "INSERT INTO menu_auth_account (id, email, password_hash, is_admin, created_at) VALUES (:id, :email, 'isolated-fixture', :admin, CURRENT_TIMESTAMP)"
                    ),
                    {"id": number, "email": email, "admin": admin},
                )
                await session.execute(
                    text(
                        "INSERT INTO menu_auth_session (account_id, token_hash, expires_at, is_revoked, created_at) VALUES (:id, :token, :expiry, FALSE, CURRENT_TIMESTAMP)"
                    ),
                    {
                        "id": number,
                        "token": menu_service.token_hash(token),
                        "expiry": menu_service.session_timestamp(
                            session,
                            dt.datetime.now(dt.UTC) + dt.timedelta(days=1),
                        ),
                    },
                )
            await session.commit()

    async def asyncTearDown(self):
        for item in reversed(self.patches):
            item.stop()
        await self.engine.dispose()
        self.directory.cleanup()

    async def test_guarded_reads_and_writes_distinguish_missing_rights_from_expiry(
        self,
    ):
        for operation in (
            lambda t: read_administration(t),
            lambda t: edit_policy(t, "agricole", "deny"),
        ):
            with self.assertRaises(SessionExpired):
                await operation("fabricated")
            with self.assertRaises(ConfigurationDenied):
                await operation("member")
        self.assertEqual(
            (await menu_service.resolve_account("member"))["id"], 2
        )
        self.assertFalse((await resolve_policy("member"))["admin"])
        await menu_service.revoke_session("owner")
        with self.assertRaises(SessionExpired):
            await read_administration("owner")

    async def test_multiple_roles_and_fresh_policy_and_deny_precedence(self):
        await edit_policy(
            "owner", "policy:account:2:role:responsable-stock", "grant"
        )
        await edit_policy(
            "owner", "policy:account:2:role:responsable-materiel", "grant"
        )
        fresh = await resolve_policy("member")
        self.assertIn("stocks:CONSULTER", fresh["permissions"])
        self.assertIn("materiel:CONSULTER", fresh["permissions"])
        await edit_policy(
            "owner",
            "policy:role:responsable-stock:permission:stocks:CONSULTER",
            "deny",
        )
        await edit_policy(
            "owner", "policy:account:2:permission:stocks:CONSULTER", "grant"
        )
        self.assertNotIn(
            "stocks:CONSULTER", (await resolve_policy("member"))["permissions"]
        )
        detail = await read_administration("owner", account_id="2")
        row = next(
            p for p in detail["permissions"] if p["key"] == "stocks:CONSULTER"
        )
        self.assertEqual(row["explicit"], "1")
        self.assertFalse(row["effective"])
        await edit_policy(
            "owner",
            "policy:role:responsable-stock:permission:stocks:CONSULTER",
            "inherit",
        )
        self.assertIn(
            "stocks:CONSULTER", (await resolve_policy("member"))["permissions"]
        )
        await edit_policy(
            "owner", "policy:account:2:role:responsable-stock", "deny"
        )
        self.assertNotIn(
            "responsable-stock", (await resolve_policy("member"))["roles"]
        )

    async def test_append_only_audit_null_before_and_inherit_after(self):
        target = "policy:account:2:permission:stocks:CONSULTER"
        await edit_policy("owner", target, "grant")
        await edit_policy("owner", target, "deny")
        await edit_policy("owner", target, "inherit")
        history = (await read_administration("owner"))["audit"]
        self.assertEqual(len(history), 3)
        self.assertEqual(
            [(r["before"], r["after"]) for r in reversed(history)],
            [
                ("Hériter", "Accorder / activer"),
                ("Accorder / activer", "Refuser / désactiver"),
                ("Refuser / désactiver", "Hériter"),
            ],
        )
        self.assertTrue(
            all(
                "owner@example.test" in r["actor"] and r["date"]
                for r in history
            )
        )
        keys = {r["id"] for r in history}
        await edit_policy("owner", target, "inherit")
        self.assertEqual(
            {r["id"] for r in (await read_administration("owner"))["audit"]},
            keys,
        )
        for key in keys:
            with self.assertRaises(ValueError):
                await edit_policy("owner", key, "deny")
        self.assertEqual(await menu_service.read_settings(), {})

    async def test_global_menu_toggle_journal_and_namespace_exclusion(self):
        await menu_service.toggle_setting("owner", "agricole")
        self.assertEqual(
            await menu_service.read_settings(), {"agricole": False}
        )
        self.assertFalse(
            any(
                e["cockpit"] == "agricole"
                for e in (await resolve_policy("owner"))["navigation"]
            )
        )
        await menu_service.toggle_setting("owner", "agricole")
        history = (await read_administration("owner"))["audit"]
        self.assertEqual(len(history), 2)
        self.assertTrue(all(r["target"] == "agricole" for r in history))
        self.assertTrue((await menu_service.read_settings())["agricole"])

    async def test_invalid_keys_ids_and_only_administrator_rollback(self):
        keys = [
            "policy:account:999:active",
            "policy:account:02:active",
            "policy:account:2 OR 1=1:active",
            "policy:account:2:role:invented",
            "policy:role:consultation:permission:stocks:INJECT",
            "x" * 201,
            "configuration",
            "configuration.menus",
        ]
        keys += [
            "policy:account:1:active",
            "policy:account:1:role:proprietaire",
            "policy:role:proprietaire:permission:parametres:MODIFIER",
            "policy:account:1:permission:parametres:CONSULTER",
        ]
        for target in keys:
            with self.subTest(target=target), self.assertRaises(ValueError):
                await edit_policy("owner", target, "deny")
        self.assertTrue((await resolve_policy("owner"))["admin"])
        self.assertEqual((await read_administration("owner"))["audit"], [])
        with self.assertRaises(ValueError):
            await read_administration(
                "owner", account_id="1; DROP TABLE menu_setting"
            )
        for value in ["0", "01", "-1", "１", "9223372036854775808", "9" * 200]:
            with self.assertRaises(ValueError):
                canonical_id(value)
        with self.assertRaises(ValueError):
            audit_key("policy:account:2:role:" + "x" * 180, None, True)
        self.assertLessEqual(
            len(
                audit_key(
                    "policy:account:9223372036854775807:permission:utilisateurs:SUPPRIMER",
                    None,
                    False,
                )
            ),
            200,
        )

    async def test_second_administrator_allows_changes_and_rechecks_actor(self):
        await edit_policy(
            "owner", "policy:account:2:role:proprietaire", "grant"
        )
        await read_administration("member")
        await edit_policy("owner", "policy:account:1:active", "deny")
        with self.assertRaises(ConfigurationDenied):
            await edit_policy("owner", "agricole", "deny")
        self.assertEqual((await menu_service.resolve_account("owner"))["id"], 1)
        await edit_policy("member", "policy:account:1:active", "grant")
        self.assertTrue((await resolve_policy("owner"))["admin"])
        await edit_policy(
            "member", "policy:account:2:role:proprietaire", "deny"
        )
        with self.assertRaises(ConfigurationDenied):
            await read_administration("member")

    async def test_role_inheritance_and_local_status_remain_authoritative(self):
        data = await read_administration("owner", role="consultation")
        row = next(
            p for p in data["permissions"] if p["key"] == "parcelles:CONSULTER"
        )
        self.assertEqual(row["explicit"], "n")
        self.assertTrue(row["inherited"])
        self.assertTrue(row["effective"])
        await edit_policy("owner", row["target"], "deny")
        denied = next(
            p
            for p in (await read_administration("owner", role="consultation"))[
                "permissions"
            ]
            if p["key"] == row["key"]
        )
        self.assertTrue(denied["inherited"])
        self.assertFalse(denied["effective"])
        await edit_policy("owner", row["target"], "inherit")
        await edit_policy(
            "owner", "policy:account:2:role:consultation", "grant"
        )
        await edit_policy("owner", "policy:account:2:active", "grant")
        with patch(
            "app.menu_policy.read_local_rights",
            return_value={"active": False, "roles": [], "overrides": {}},
        ):
            self.assertEqual(
                (await resolve_policy("member"))["permissions"], []
            )

    async def test_concurrent_administrators_cannot_both_disable_themselves(
        self,
    ):
        await edit_policy(
            "owner", "policy:account:2:role:proprietaire", "grant"
        )
        results = await asyncio.gather(
            edit_policy("owner", "policy:account:1:active", "deny"),
            edit_policy("member", "policy:account:2:active", "deny"),
            return_exceptions=True,
        )
        self.assertEqual(sum(isinstance(r, ValueError) for r in results), 1)
        self.assertEqual(sum(r is None for r in results), 1)
        policies = [
            await resolve_policy("owner"),
            await resolve_policy("member"),
        ]
        self.assertEqual(sum(p["admin"] for p in policies), 1)

    async def test_only_real_accounts_and_search_empty_state(self):
        data = await read_administration("owner")
        self.assertEqual([r["id"] for r in data["accounts"]], ["1", "2"])
        self.assertEqual(
            (await read_administration("owner", search="nonexistent"))[
                "accounts"
            ],
            [],
        )
        self.assertEqual(
            (await read_administration("owner", search="member"))["accounts"][
                0
            ]["id"],
            "2",
        )
        self.assertEqual(len(data["roles"]), 10)
        self.assertEqual(
            (
                await read_administration(
                    "owner", account_filter="Administrateurs"
                )
            )["account_total"],
            1,
        )
        await edit_policy("owner", "policy:account:2:active", "deny")
        inactive = await read_administration(
            "owner", account_filter="Désactivés"
        )
        self.assertEqual(inactive["account_total"], 1)
        self.assertEqual(inactive["accounts"][0]["id"], "2")
        async with self.factory() as session:
            self.assertEqual(
                int(
                    (
                        await session.execute(
                            text("SELECT COUNT(*) FROM menu_auth_account")
                        )
                    ).scalar()
                ),
                2,
            )


class Context(SimpleNamespace):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get_state(self, state_class):
        return self.auth

    def _clear_sensitive(self):
        MenuConfigurationState._clear_sensitive(self)


class ConfigurationRefreshTests(unittest.IsolatedAsyncioTestCase):
    def context(self):
        return Context(
            auth=SimpleNamespace(token="valid", authenticated=True, admin=True),
            _generation=0,
            selected_role="",
            selected_account="",
            account_search="",
            account_filter="Tous",
            account_offset=0,
            audit_offset=0,
            rows=[{"key": "sensitive"}],
            roles=[{}],
            accounts=[{}],
            permissions=[{}],
            assignments=[{}],
            audit=[{}],
            allowed=True,
            saving=True,
            notice="",
            error="",
        )

    async def run_event(self, handler, state, *args):
        result = inspect.unwrap(handler.fn)(state, *args)
        return [event async for event in result]

    async def test_success_yields_immediate_navigation_and_configuration_refresh(
        self,
    ):
        state = self.context()
        with patch(
            "app.states.menu_configuration_state.edit_policy",
            new_callable=AsyncMock,
        ):
            events = await self.run_event(
                MenuConfigurationState.save_edit, state, "agricole", "toggle"
            )
        self.assertIs(events[0], NavigationState.refresh_navigation)
        self.assertIs(events[1], MenuConfigurationState.load_configuration)
        self.assertFalse(state.saving)
        self.assertTrue(state.notice)

    async def test_missing_rights_clears_sensitive_data_without_revoking_login(
        self,
    ):
        state = self.context()
        with patch(
            "app.states.menu_configuration_state.read_administration",
            new_callable=AsyncMock,
            side_effect=ConfigurationDenied("Droits requis"),
        ):
            await self.run_event(
                MenuConfigurationState.load_configuration, state
            )
        self.assertEqual(state.auth.token, "valid")
        self.assertTrue(state.auth.authenticated)
        for name in [
            "rows",
            "roles",
            "accounts",
            "permissions",
            "assignments",
            "audit",
        ]:
            self.assertEqual(getattr(state, name), [])
        self.assertFalse(state.allowed)

    async def test_expired_read_clears_login_but_missing_rights_does_not(self):
        state = self.context()
        with patch(
            "app.states.menu_configuration_state.read_administration",
            new_callable=AsyncMock,
            side_effect=SessionExpired("Session expirée"),
        ):
            await self.run_event(
                MenuConfigurationState.load_configuration, state
            )
        self.assertEqual(state.auth.token, "")
        self.assertFalse(state.auth.authenticated)
        self.assertFalse(state.allowed)
        self.assertEqual(state.audit, [])
        self.assertEqual(state.auth.error, "Session expirée")

    async def test_old_load_cannot_publish_after_sensitive_clear(self):
        state = self.context()

        async def read(*args, **kwargs):
            state._clear_sensitive()
            return {}

        with patch(
            "app.states.menu_configuration_state.read_administration",
            side_effect=read,
        ):
            await self.run_event(
                MenuConfigurationState.load_configuration, state
            )
        self.assertFalse(state.allowed)
        self.assertEqual(state.accounts, [])


if __name__ == "__main__":
    unittest.main()

import reflex as rx

import ast
import datetime as dt
import importlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import menu_service
from app.menu_database import menu_metadata
from app.server_guard import (
    CHECKED_CONTEXT,
    EVENT_COVERAGE,
    VALID_PERMISSIONS,
    EventRule,
    authorize_event,
    build_rule,
    business_states,
    checked_service,
    install_event_gate,
    wrap_event,
)
from app.states.menu_auth_state import MenuAuthState
from app.states.menu_configuration_state import MenuConfigurationState
from app.states.navigation_state import (
    NavigationState,
    resolve_navigation_entry,
)


class Context(SimpleNamespace):
    async def __aenter__(self):
        self.locked = True
        return self

    async def __aexit__(self, *args):
        self.locked = False

    async def get_state(self, state_class):
        return self.states.setdefault(state_class, state_class())


async def emitted(handler, context, *args):
    result = handler.fn(context, *args)
    return [event async for event in result]


def context(
    token: str, path: str = "/parcelles", entry: str = "agricole.parcelles"
) -> Context:
    auth = MenuAuthState()
    auth.token = token
    auth.ready = True
    auth.authenticated = bool(token)
    auth.verified_path = path
    auth._verified_token = token
    auth.requested_entry = entry
    auth._generation = 1
    return Context(
        states={
            MenuAuthState: auth,
            NavigationState: NavigationState(),
            MenuConfigurationState: MenuConfigurationState(),
        },
        router=SimpleNamespace(url=SimpleNamespace(path=path)),
        locked=False,
        ran=0,
        register="ventes",
        form_kind="sale",
    )


READ = EventRule(
    "ParcelsState", "filter", ("parcelles",), ("CONSULTER",), ("/parcelles",)
)
WRITE = EventRule(
    "ParcelsState", "write", ("parcelles",), ("MODIFIER",), ("/parcelles",)
)
EXPORT = EventRule(
    "ParcelsState", "export", ("parcelles",), ("EXPORTER",), ("/parcelles",)
)


class GateDatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.directory.name}/menu.db"
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
        ]
        for item in self.patches:
            item.start()
        self.owner_token, self.owner = await menu_service.authenticate(
            "owner@example.test", "isolated-owner-password", True
        )
        self.reader_token, self.reader = await menu_service.authenticate(
            "reader@example.test", "isolated-reader-password", True
        )
        await self.setting(
            f"policy:account:{self.reader['id']}:role:consultation", True
        )

    async def asyncTearDown(self):
        for item in reversed(self.patches):
            item.stop()
        await self.engine.dispose()
        self.directory.cleanup()

    async def setting(self, key: str, enabled: bool):
        async with self.factory() as session:
            await session.execute(
                text("DELETE FROM menu_setting WHERE navigation_key = :key"),
                {"key": key},
            )
            await session.execute(
                text(
                    "INSERT INTO menu_setting (navigation_key, enabled, updated_at, updated_by_account_id) VALUES (:key, :enabled, CURRENT_TIMESTAMP, :id)"
                ),
                {"key": key, "enabled": enabled, "id": self.owner["id"]},
            )
            await session.commit()

    async def test_anonymous_does_not_run_business_code(self):
        def implementation(state):
            state.ran += 1

        handler = rx.event.EventHandler(fn=implementation)
        wrap_event(handler, READ)
        state = context("")
        events = await emitted(handler, state)
        self.assertEqual(state.ran, 0)
        self.assertEqual(len(events), 1)
        auth = await state.get_state(MenuAuthState)
        self.assertFalse(auth.authenticated)
        self.assertEqual(
            (await state.get_state(NavigationState)).visible_navigation, []
        )

    async def test_reader_can_filter_but_not_write_or_export(self):
        state = context(self.reader_token)
        self.assertTrue(await authorize_event(state, READ))
        self.assertFalse(await authorize_event(state, WRITE))
        self.assertFalse(await authorize_event(state, EXPORT))
        auth = await state.get_state(MenuAuthState)
        self.assertEqual(auth.token, self.reader_token)
        self.assertTrue(auth.authenticated)
        self.assertTrue(auth.page_allowed)

    async def test_account_and_role_denies_win_over_owner_and_account_grant(
        self,
    ):
        state = context(self.owner_token)
        self.assertTrue(await authorize_event(state, WRITE))
        await self.setting(
            f"policy:account:{self.owner['id']}:permission:parcelles:MODIFIER",
            False,
        )
        self.assertFalse(await authorize_event(state, WRITE))
        await self.setting(
            f"policy:account:{self.owner['id']}:permission:parcelles:MODIFIER",
            True,
        )
        await self.setting(
            "policy:role:proprietaire:permission:parcelles:MODIFIER", False
        )
        self.assertFalse(await authorize_event(state, WRITE))
        self.assertTrue((await state.get_state(MenuAuthState)).authenticated)

    async def test_expiry_and_revocation_clear_stale_session_views(self):
        for expired in (True, False):
            state = context(self.owner_token)
            async with self.factory() as session:
                await session.execute(
                    text(
                        "UPDATE menu_auth_session SET is_revoked = :revoked, expires_at = :expires WHERE token_hash = :token"
                    ),
                    {
                        "revoked": not expired,
                        "expires": dt.datetime.now(dt.UTC).replace(tzinfo=None)
                        + dt.timedelta(days=-1 if expired else 1),
                        "token": menu_service.token_hash(self.owner_token),
                    },
                )
                await session.commit()
            with patch("app.server_guard.logging.exception") as log:
                self.assertFalse(await authorize_event(state, WRITE))
            log.assert_not_called()
            auth = await state.get_state(MenuAuthState)
            self.assertEqual(auth.token, "")
            self.assertEqual(auth._verified_token, "")
            self.assertEqual(auth.permissions, [])
            self.assertFalse(auth.page_allowed)
            self.assertEqual(
                (await state.get_state(MenuConfigurationState)).rows, []
            )

    async def test_verified_route_and_token_are_not_client_permissions(self):
        for changed in (
            "ready",
            "authenticated",
            "verified_path",
            "_verified_token",
            "requested_entry",
        ):
            state = context(self.owner_token)
            auth = await state.get_state(MenuAuthState)
            setattr(
                auth,
                changed,
                False if changed in {"ready", "authenticated"} else "invalid",
            )
            auth.page_allowed = True
            auth.permissions = ["parcelles:MODIFIER"]
            self.assertFalse(await authorize_event(state, WRITE), changed)
        state = context(self.owner_token, "/crm", "agricole.parcelles")
        self.assertFalse(await authorize_event(state, WRITE))
        state = context(self.owner_token, "/unregistered", "agricole.parcelles")
        self.assertFalse(await authorize_event(state, WRITE))

    async def test_repeat_refresh_reload_and_allowed_business_payload(self):
        async def implementation(state, value: str):
            state.ran += 1
            state.value = value
            return rx.toast("Enregistré")

        handler = rx.event.EventHandler(fn=implementation)
        wrap_event(handler, WRITE)
        for state in (context(self.owner_token), context(self.owner_token)):
            for _ in range(3):
                self.assertTrue(await authorize_event(state, READ))
            events = await emitted(handler, state, "Parcelle Nord")
            self.assertEqual(state.ran, 1)
            self.assertEqual(state.value, "Parcelle Nord")
            self.assertEqual(len(events), 1)
            self.assertIsNone(CHECKED_CONTEXT.get())

    async def test_direct_crm_queries_and_configuration(self):
        cockpits = {
            "clients": "commercial",
            "fournisseurs": "achats",
            "ventes": "commercial",
            "achats": "achats",
            "creances": "financier",
            "dettes": "financier",
            "paiements": "financier",
            "rapports": "commercial",
        }
        for tab, cockpit in cockpits.items():
            entry = resolve_navigation_entry("crm", cockpit, tab)
            self.assertEqual(entry["tab"], tab)
            state = context(self.owner_token, "/crm", entry["key"])
            rule = EventRule(
                "CrmRegistersState",
                "enter_register",
                ("ventes", "achats", "comptabilite"),
                ("CONSULTER",),
                ("/crm",),
            )
            self.assertTrue(await authorize_event(state, rule, ("ventes",)))
        state = context(
            self.reader_token, "/configuration", "configuration.menus"
        )
        config_rule = EventRule(
            "Service",
            "configuration",
            ("parametres",),
            ("MODIFIER",),
            ("/configuration",),
        )
        self.assertFalse(await authorize_event(state, config_rule))
        state = context(
            self.owner_token, "/configuration", "configuration.menus"
        )
        self.assertTrue(await authorize_event(state, config_rule))

    async def test_alternate_entry_never_grants_another_module(self):
        await self.setting(
            f"policy:account:{self.reader['id']}:permission:stocks:MODIFIER",
            True,
        )
        state = context(self.reader_token, "/traitements", "stocks.magasin")
        rule = EventRule(
            "OperationsState",
            "submit_intervention",
            ("interventions",),
            ("CREER",),
            ("/traitements",),
        )
        self.assertFalse(await authorize_event(state, rule))
        self.assertTrue((await state.get_state(MenuAuthState)).authenticated)

    async def test_services_require_checked_context_and_recheck_denies(self):
        @checked_service(("parcelles", "MODIFIER"))
        async def service(state):
            state.ran += 1

        state = context(self.owner_token)
        with self.assertRaises(PermissionError):
            await service(state)

        async def implementation(state):
            await service(state)

        handler = rx.event.EventHandler(fn=implementation)
        wrap_event(handler, WRITE)
        await emitted(handler, state)
        self.assertEqual(state.ran, 1)
        await self.setting(
            f"policy:account:{self.owner['id']}:permission:parcelles:MODIFIER",
            False,
        )
        await emitted(handler, state)
        self.assertEqual(state.ran, 1)

    async def test_background_resolves_outside_state_lock(self):
        state = context(self.reader_token)
        from app.menu_policy import resolve_policy

        async def resolve(token):
            self.assertFalse(state.locked)
            return await resolve_policy(token)

        with patch("app.server_guard.resolve_policy", side_effect=resolve):
            self.assertTrue(await authorize_event(state, READ, background=True))
        self.assertFalse(state.locked)


class InventoryTests(unittest.IsolatedAsyncioTestCase):
    def test_search_load_is_read_only_without_changing_stock_action(self):
        from app.states.search_state import SearchState
        from app.states.stock_state import StockState

        rule = build_rule(
            SearchState,
            "load_search",
            SearchState.event_handlers["load_search"],
        )
        self.assertEqual(rule.actions, ("CONSULTER",))
        self.assertTrue(rule.modules)
        self.assertEqual(rule.routes, ("/recherche",))
        for module in rule.modules:
            for action in rule.actions:
                self.assertIn((module, action), VALID_PERMISSIONS)

        stock_rule = build_rule(
            StockState,
            "decide_stock",
            StockState.event_handlers["decide_stock"],
        )
        self.assertEqual(stock_rule.actions, ("MODIFIER",))

    async def test_every_imported_business_state_and_public_event_is_gated(
        self,
    ):
        for path in Path("app/states").glob("*_state.py"):
            importlib.import_module(f"app.states.{path.stem}")
        install_event_gate()
        expected = set()
        for state_class in business_states():
            for name, handler in state_class.event_handlers.items():
                if name.startswith("_"):
                    continue
                key = f"{state_class.get_full_name()}.{name}"
                expected.add(key)
                self.assertTrue(
                    getattr(handler.fn, "_agripro_event_gate", False), key
                )
                with patch(
                    "app.server_guard.authorize_event",
                    new=AsyncMock(return_value=False),
                ):
                    events = await emitted(handler, context(""))
                self.assertEqual(len(events), 1, key)
        self.assertTrue(expected)
        self.assertEqual(set(EVENT_COVERAGE), expected)
        identities = {
            key: id(handler.fn)
            for state_class in business_states()
            for key, handler in state_class.event_handlers.items()
        }
        install_event_gate()
        self.assertTrue(
            all(
                getattr(handler.fn, "_agripro_event_gate", False)
                for state_class in business_states()
                for name, handler in state_class.event_handlers.items()
                if not name.startswith("_")
            )
        )
        self.assertTrue(identities)

    def test_installation_precedes_page_registration(self):
        tree = ast.parse(Path("app/app.py").read_text())
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        install = next(
            node.lineno
            for node in calls
            if isinstance(node.func, ast.Name)
            and node.func.id == "install_event_gate"
        )
        registrations = [
            node.lineno
            for node in calls
            if isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_page"
        ]
        self.assertTrue(all(install < line for line in registrations))

    async def test_actual_python_api_surfaces_reject_anonymous_before_io(self):
        from app.phenology_api import get_culture_stages, post_observation
        from app.admin_operations import complete_task
        from app.admin_users import change_user_status

        with patch(
            "app.phenology_api.ensure_local_database", new=AsyncMock()
        ) as database:
            for fn, args in (
                (get_culture_stages, (1,)),
                (post_observation, (1, "Stade", "2025-01-01", "Agent")),
                (complete_task, (1, 1)),
                (change_user_status, (1, 2, "SUSPENDRE")),
            ):
                with self.assertRaises(PermissionError):
                    await fn(*args)
        database.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()

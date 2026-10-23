import reflex as rx

import ast
import inspect
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.auth_dispatch import safe_destination
from app.navigation import ROUTE_MATRIX
from app.states.menu_auth_state import MenuAuthState
from app.states.navigation_state import NavigationState
from app.menu_policy import evaluate_policy


class Context(SimpleNamespace):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get_state(self, state_class):
        if state_class.__name__ == "MenuConfigurationState":
            return self.config
        return self.nav


async def events(handler, state, *args):
    result = inspect.unwrap(handler.fn)(state, *args)
    return [event async for event in result]


def context(token=""):
    return Context(
        token=token,
        ready=False,
        authenticated=False,
        admin=False,
        email="",
        error="",
        verified_path="",
        _verified_token="",
        _generation=1,
        _pending_loader="",
        return_path="/parcelles",
        _dispatch_page="",
        _dispatch_index=0,
        busy=False,
        signup=False,
        requested_entry="agricole.parcelles",
        page_allowed=False,
        permissions=[],
        allowed_crm_tabs=[],
        has_modules=False,
        nav=NavigationState(),
    )


class EntryTests(unittest.IsolatedAsyncioTestCase):
    async def test_every_anonymous_destination_excludes_loaders(self):
        for page in ROUTE_MATRIX:
            state = context()
            with patch(
                "app.states.menu_auth_state.resolve_policy",
                new_callable=AsyncMock,
            ) as resolve:
                emitted = await events(
                    MenuAuthState.verify_page, state, page, 1
                )
            resolve.assert_not_awaited()
            self.assertFalse(state.authenticated)
            self.assertTrue(state.ready)
            self.assertEqual(state._pending_loader, "")
            self.assertEqual(len(emitted), int(page != "cockpit"))

    async def test_restored_session_dispatches_only_after_resolution(self):
        state = context("valid")
        account = evaluate_policy(
            {"id": 8, "email": "existing@example.com", "admin": False},
            {"policy:account:8:role:consultation": True},
        )
        with patch(
            "app.states.menu_auth_state.resolve_policy",
            new_callable=AsyncMock,
            return_value=account,
        ) as resolve:
            emitted = await events(
                MenuAuthState.verify_page, state, "parcelles", 1
            )
        resolve.assert_awaited_once_with("valid")
        self.assertEqual(len(emitted), 1)
        self.assertTrue(state.authenticated)
        self.assertEqual(state.verified_path, "/parcelles")
        self.assertEqual(state._verified_token, "valid")

    async def test_unassigned_session_never_dispatches_business_loader(self):
        state = context("unassigned")
        policy = evaluate_policy(
            {"id": 8, "email": "unassigned@example.test", "admin": False}, {}
        )
        with patch(
            "app.states.menu_auth_state.resolve_policy",
            new_callable=AsyncMock,
            return_value=policy,
        ):
            emitted = await events(
                MenuAuthState.verify_page, state, "parcelles", 1
            )
        self.assertEqual(emitted, [])
        self.assertTrue(state.authenticated)
        self.assertFalse(state.page_allowed)
        self.assertFalse(state.has_modules)
        self.assertEqual(state.nav.visible_navigation, [])

    async def test_loader_rechecks_a_changed_policy(self):
        state = context("revoked-rights")
        state.authenticated = True
        state.page_allowed = True
        policy = evaluate_policy(
            {"id": 8, "email": "reader@example.test", "admin": False}, {}
        )
        with (
            patch(
                "app.states.menu_auth_state.resolve_policy",
                new_callable=AsyncMock,
                return_value=policy,
            ) as resolve,
            patch.dict(
                "app.states.menu_auth_state.PAGE_LOADERS", {"parcelles": ()}
            ),
        ):
            emitted = await events(
                MenuAuthState.dispatch_loader, state, "parcelles", 0, 1
            )
        resolve.assert_awaited_once_with("revoked-rights")
        self.assertEqual(emitted, [])
        self.assertFalse(state.page_allowed)
        self.assertEqual(state._pending_loader, "")

    async def test_expired_session_never_dispatches_business_loader(self):
        state = context("expired")
        with patch(
            "app.states.menu_auth_state.resolve_policy",
            new_callable=AsyncMock,
            side_effect=PermissionError("expired"),
        ):
            emitted = await events(
                MenuAuthState.verify_page, state, "parcelles", 1
            )
        self.assertEqual(state.token, "")
        self.assertFalse(state.authenticated)
        self.assertEqual(state.verified_path, "")
        self.assertEqual(len(emitted), 1)

    async def test_old_restore_cannot_publish_after_logout(self):
        state = context("old")

        async def resolve(token):
            state._generation += 1
            state.token = ""
            return {"id": 1, "email": "old@example.com", "admin": True}

        with patch(
            "app.states.menu_auth_state.resolve_policy", side_effect=resolve
        ):
            emitted = await events(
                MenuAuthState.verify_page, state, "parcelles", 1
            )
        self.assertEqual(emitted, [])
        self.assertFalse(state.authenticated)

    async def test_login_returns_to_registered_destination(self):
        state = context()
        account = {"id": 1, "email": "existing@example.com", "admin": False}
        with patch(
            "app.states.menu_auth_state.authenticate",
            new_callable=AsyncMock,
            return_value=("session", account),
        ):
            emitted = await events(
                MenuAuthState.authenticate_account,
                state,
                account["email"],
                "not-stored-password",
            )
        self.assertEqual(len(emitted), 2)
        self.assertEqual(state.return_path, "/")
        self.assertEqual(state.verified_path, "")
        self.assertFalse(hasattr(state, "password"))

    async def test_logout_revokes_and_purges_navigation(self):
        state = context("session")
        state.authenticated = True
        state.nav.cockpits = [{"key": "global"}]
        state.nav.visible_navigation = [{"key": "global.overview"}]
        state.config = SimpleNamespace(
            rows=[1], allowed=True, error="", notice="", _generation=0
        )
        with patch(
            "app.states.menu_auth_state.revoke_session", new_callable=AsyncMock
        ) as revoke:
            await events(MenuAuthState.logout, state)
        revoke.assert_awaited_once_with("session")
        self.assertEqual(state.token, "")
        self.assertFalse(state.authenticated)
        self.assertEqual(state.nav.cockpits, [])
        self.assertEqual(state.nav.visible_navigation, [])
        self.assertEqual(state.config.rows, [])
        self.assertTrue(state.ready)

    def test_redirect_allowlist(self):
        for value in (
            "https://evil.example",
            "//evil.example",
            "/unknown",
            "/\\evil",
            "/%2f%2fevil",
            "/crm\n",
        ):
            self.assertEqual(safe_destination(value), "/")
        self.assertEqual(
            safe_destination(
                "/crm?cockpit=achats&vue=achats&next=https://evil.example"
            ),
            "/crm?cockpit=achats&vue=achats",
        )
        self.assertEqual(
            safe_destination("/traitements#nav-magasin"),
            "/traitements#nav-magasin",
        )

    def test_all_routes_have_one_guarded_on_load(self):
        tree = ast.parse(Path("app/app.py").read_text())
        registrations = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_page"
        ]
        self.assertEqual(len(registrations), len(ROUTE_MATRIX))
        for registration in registrations:
            on_load = next(
                k.value for k in registration.keywords if k.arg == "on_load"
            )
            self.assertIsInstance(on_load, ast.Call)
            self.assertEqual(on_load.func.attr, "enter_page")


if __name__ == "__main__":
    unittest.main()

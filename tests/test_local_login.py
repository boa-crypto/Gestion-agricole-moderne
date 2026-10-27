import reflex as rx

import ast
import inspect
import secrets
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import menu_service as service
from app.menu_database import menu_metadata
from app.states.menu_auth_state import MenuAuthState


class LoginWiringTests(unittest.TestCase):
    def test_config_uses_reflex_without_external_auth_plugin(self):
        tree = ast.parse(Path("rxconfig.py").read_text())
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        config = next(
            node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "config"
                for target in node.targets
            )
        )
        self.assertEqual(ast.unparse(config.func), "rx.Config")
        self.assertFalse(
            any(
                isinstance(call.func, ast.Attribute)
                and call.func.attr == "AuthPlugin"
                or isinstance(call.func, ast.Name)
                and call.func.id == "AuthPlugin"
                for call in calls
            )
        )
        plugins = next(
            item.value for item in config.keywords if item.arg == "plugins"
        )
        self.assertEqual(
            [ast.unparse(plugin.func) for plugin in plugins.elts],
            ["rx.plugins.SitemapPlugin", "rx.plugins.TailwindV4Plugin"],
        )
        self.assertNotIn("app.pages.auth_login", ast.unparse(tree))
        app_tree = ast.parse(Path("app/app.py").read_text())
        app = next(
            node.value
            for node in app_tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "app"
                for target in node.targets
            )
        )
        self.assertEqual(ast.unparse(app.func), "rxe.App")

    def test_first_visit_invitation_has_accessible_mode_switch(self):
        tree = ast.parse(Path("app/components/menu_auth.py").read_text())
        panel = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "login_panel"
        )
        self.assertIn(
            "Première visite ? Créez votre compte pour accéder à AgriPro.",
            [
                node.value
                for node in ast.walk(panel)
                if isinstance(node, ast.Constant)
            ],
        )
        button = next(
            node
            for node in ast.walk(panel)
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "rx.el.button"
            and any(
                isinstance(arg, ast.Constant)
                and arg.value == "Créer mon compte"
                for arg in node.args
            )
        )
        props = {item.arg: ast.unparse(item.value) for item in button.keywords}
        self.assertEqual(props["on_click"], "MenuAuthState.change_mode")
        self.assertEqual(props["type"], "'button'")
        self.assertEqual(props["disabled"], "MenuAuthState.busy")
        self.assertEqual(props["aria_describedby"], "'auth-first-visit'")
        self.assertIn("focus-visible:", props["class_name"])
        state = SimpleNamespace(signup=False, error="Previous error")
        MenuAuthState.change_mode.fn(state)
        self.assertTrue(state.signup)
        self.assertEqual(state.error, "")
        MenuAuthState.change_mode.fn(state)
        self.assertFalse(state.signup)


class LoginContext(SimpleNamespace):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class LocalLoginTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{temporary.name}/menu-login-test.db"
        )
        self.addAsyncCleanup(self.engine.dispose)
        async with self.engine.begin() as connection:
            await connection.run_sync(menu_metadata().create_all)
        self.factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.enterContext(patch.object(service, "menu_session", self.factory))
        self.enterContext(
            patch.object(service, "ensure_menu_database", AsyncMock())
        )
        self.email = f"{secrets.token_hex(8)}@example.test"
        self.password = secrets.token_urlsafe(24)

    async def authenticate_form(self, signup: bool, token: str = ""):
        state = LoginContext(
            signup=signup,
            token=token,
            busy=True,
            authenticated=False,
            admin=False,
            email="",
            error="",
            ready=False,
            verified_path="",
            _verified_token="",
            return_path="/parcelles",
        )
        handler = inspect.unwrap(MenuAuthState.authenticate_account.fn)
        emitted = [
            event async for event in handler(state, self.email, self.password)
        ]
        self.assertEqual(len(emitted), 2)
        self.assertTrue(state.authenticated)
        self.assertTrue(state.ready)
        self.assertFalse(state.busy)
        self.assertEqual(state.error, "")
        self.assertEqual(state.verified_path, "")
        self.assertEqual(state.return_path, "/")
        self.assertFalse(hasattr(state, "password"))
        return state

    async def test_empty_database_signup_then_first_account_login(self):
        async with self.factory() as session:
            count = (
                await session.execute(
                    text("SELECT COUNT(*) FROM menu_auth_account")
                )
            ).scalar_one()
        self.assertEqual(count, 0)
        signup = await self.authenticate_form(True)
        account = await service.resolve_account(signup.token)
        self.assertTrue(signup.admin)
        self.assertTrue(account["admin"])
        self.assertEqual(account["email"], self.email)
        await service.revoke_session(signup.token)
        with self.assertRaises(PermissionError):
            await service.resolve_account(signup.token)
        await self.engine.dispose()
        login = await self.authenticate_form(False)
        self.assertEqual(await service.resolve_account(login.token), account)
        self.assertTrue(login.admin)
        self.assertNotEqual(login.token, signup.token)
        async with self.factory() as session:
            stored = (
                await session.execute(
                    text("SELECT password_hash FROM menu_auth_account LIMIT 1")
                )
            ).scalar_one()
            count = (
                await session.execute(
                    text("SELECT COUNT(*) FROM menu_auth_account")
                )
            ).scalar_one()
        self.assertEqual(count, 1)
        self.assertNotEqual(stored, self.password)
        self.assertTrue(service.verify_password(self.password, stored))
        _, next_account = await service.authenticate(
            f"{secrets.token_hex(8)}@example.test",
            secrets.token_urlsafe(24),
            True,
        )
        self.assertFalse(next_account["admin"])

    async def test_validation_and_wrong_password_do_not_create_sessions(self):
        for email, password in (
            ("invalid", self.password),
            (self.email, "short"),
            (self.email, "x" * 257),
        ):
            with self.subTest(
                email_valid=email == self.email, length=len(password)
            ):
                with self.assertRaises(ValueError):
                    await service.authenticate(email, password, True)
        async with self.factory() as session:
            self.assertEqual(
                (
                    await session.execute(
                        text("SELECT COUNT(*) FROM menu_auth_account")
                    )
                ).scalar_one(),
                0,
            )
        await service.authenticate(self.email, self.password, True)
        with self.assertRaises(ValueError):
            await service.authenticate(
                self.email, secrets.token_urlsafe(24), False
            )
        async with self.factory() as session:
            self.assertEqual(
                (
                    await session.execute(
                        text("SELECT COUNT(*) FROM menu_auth_session")
                    )
                ).scalar_one(),
                1,
            )


if __name__ == "__main__":
    unittest.main()

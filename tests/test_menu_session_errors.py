import reflex as rx

import ast
import inspect
import textwrap
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.states.menu_auth_state import MenuAuthState
from app.states.menu_configuration_state import MenuConfigurationState
from app.menu_policy_admin import ConfigurationDenied, SessionExpired


class EventContext(SimpleNamespace):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get_state(self, state_class):
        if state_class is MenuConfigurationState:
            return self.config
        return self.auth

    def _clear_sensitive(self):
        MenuConfigurationState._clear_sensitive(self)


async def run_handler(handler: rx.event.EventHandler, context, *args):
    # Exercise the underlying handler, not Reflex's background dispatch wrapper.
    result = inspect.unwrap(handler.fn)(context, *args)
    events = []
    if inspect.isasyncgen(result):
        async for event in result:
            events.append(event)
    else:
        await result
    return events


class SessionErrorTests(unittest.IsolatedAsyncioTestCase):
    def auth_context(self, token="", admin=False, ready=True):
        return EventContext(
            token=token,
            authenticated=bool(token),
            admin=admin,
            ready=ready,
            email="admin@example.com" if token else "",
            error="",
            signup=False,
            busy=True,
            config=MenuConfigurationState(),
        )

    def configuration_context(self, auth):
        return EventContext(
            auth=auth,
            _generation=0,
            loading=True,
            allowed=True,
            rows=[],
            error="",
            notice="",
            saving=True,
            selected_role="",
            selected_account="",
            account_search="",
            account_filter="Tous",
            account_offset=0,
            audit_offset=0,
        )

    async def test_anonymous_and_known_non_admin_skip_admin_read(self):
        for token, admin, ready in (
            ("", False, False),
            ("viewer", False, True),
        ):
            with self.subTest(token=token):
                state = self.configuration_context(
                    self.auth_context(token, admin, ready)
                )
                with (
                    patch(
                        "app.states.menu_configuration_state.read_administration",
                        new_callable=AsyncMock,
                        side_effect=SessionExpired("Connexion requise")
                        if not token
                        else ConfigurationDenied("Droits requis"),
                    ) as read,
                    patch("logging.exception") as log,
                ):
                    await run_handler(
                        MenuConfigurationState.load_configuration, state
                    )
                read.assert_awaited_once()
                log.assert_not_called()
                self.assertFalse(state.loading)
                self.assertFalse(state.allowed)
                self.assertEqual(state.rows, [])
                self.assertTrue(state.error)

    async def test_denied_admin_read_clears_stale_session_quietly(self):
        auth = self.auth_context("expired", True)
        state = self.configuration_context(auth)
        with (
            patch(
                "app.states.menu_configuration_state.read_administration",
                new_callable=AsyncMock,
                side_effect=SessionExpired("expired"),
            ),
            patch("logging.exception") as log,
        ):
            await run_handler(MenuConfigurationState.load_configuration, state)
        log.assert_not_called()
        self.assertEqual(auth.token, "")
        self.assertFalse(auth.authenticated)
        self.assertFalse(auth.admin)
        self.assertTrue(auth.ready)
        self.assertTrue(auth.error)
        self.assertFalse(state.loading)
        self.assertFalse(state.allowed)
        self.assertEqual(state.rows, [])

    async def test_old_denial_does_not_clear_new_session(self):
        auth = self.auth_context("old", True)
        state = self.configuration_context(auth)

        async def denied(*args, **kwargs):
            auth.token = "new"
            raise SessionExpired("expired")

        with (
            patch(
                "app.states.menu_configuration_state.read_administration",
                side_effect=denied,
            ),
            patch("logging.exception") as log,
        ):
            await run_handler(MenuConfigurationState.load_configuration, state)
        log.assert_not_called()
        self.assertEqual(auth.token, "new")
        self.assertTrue(auth.authenticated)

    async def test_restore_missing_or_expired_session_is_routine(self):
        for token in ("", "expired"):
            with self.subTest(token=token):
                auth = self.auth_context(token, True)
                with (
                    patch(
                        "app.states.menu_auth_state.resolve_policy",
                        new_callable=AsyncMock,
                        side_effect=PermissionError("expired"),
                    ) as resolve,
                    patch("logging.exception") as log,
                ):
                    events = await run_handler(
                        MenuAuthState.restore_session, auth
                    )
                log.assert_not_called()
                self.assertEqual(resolve.await_count, int(bool(token)))
                self.assertEqual(auth.token, "")
                self.assertFalse(auth.authenticated)
                self.assertFalse(auth.admin)
                self.assertTrue(auth.ready)
                self.assertEqual(len(events), 1)

    async def test_invalid_credentials_and_validation_do_not_log(self):
        for error in (
            ValueError("Identifiants incorrects."),
            PermissionError("Accès refusé."),
        ):
            with self.subTest(error=type(error).__name__):
                auth = self.auth_context()
                with (
                    patch(
                        "app.states.menu_auth_state.authenticate",
                        new_callable=AsyncMock,
                        side_effect=error,
                    ),
                    patch("logging.exception") as log,
                ):
                    await run_handler(
                        MenuAuthState.authenticate_account,
                        auth,
                        "user@example.com",
                        "incorrect",
                    )
                log.assert_not_called()
                self.assertEqual(auth.error, str(error))
                self.assertFalse(auth.busy)

    async def test_toggle_denial_keeps_feedback_and_resets_state(self):
        state = self.configuration_context(self.auth_context("expired", True))
        with (
            patch(
                "app.states.menu_configuration_state.edit_policy",
                new_callable=AsyncMock,
                side_effect=PermissionError("expired"),
            ),
            patch("logging.exception") as log,
        ):
            events = await run_handler(
                MenuConfigurationState.save_edit, state, "agricole", "toggle"
            )
        log.assert_not_called()
        self.assertFalse(state.saving)
        self.assertFalse(state.allowed)
        self.assertEqual(state.rows, [])
        self.assertTrue(state.error)
        self.assertEqual(len(events), 2)

    def test_target_handlers_have_no_try_statements(self):
        for handler in (
            MenuConfigurationState.save_edit,
            MenuAuthState.restore_session,
            MenuAuthState.authenticate_account,
        ):
            with self.subTest(handler=handler.fn.__name__):
                tree = ast.parse(
                    textwrap.dedent(
                        inspect.getsource(inspect.unwrap(handler.fn))
                    )
                )
                self.assertFalse(
                    any(
                        isinstance(node, (ast.Try, ast.TryStar))
                        for node in ast.walk(tree)
                    )
                )

    async def test_toggle_validation_remains_quiet(self):
        state = self.configuration_context(self.auth_context("admin", True))
        error = ValueError("Ce menu ne peut pas être modifié.")
        with (
            patch(
                "app.states.menu_configuration_state.edit_policy",
                new_callable=AsyncMock,
                side_effect=error,
            ),
            patch("logging.exception") as exception_log,
            patch("logging.error") as error_log,
        ):
            events = await run_handler(
                MenuConfigurationState.save_edit,
                state,
                "configuration",
                "toggle",
            )
        exception_log.assert_not_called()
        error_log.assert_not_called()
        self.assertEqual(state.error, str(error))
        self.assertFalse(state.saving)
        self.assertEqual(len(events), 1)

    async def test_successful_authentication_keeps_events_and_cleanup(self):
        for signup in (False, True):
            with self.subTest(signup=signup):
                auth = self.auth_context()
                auth.signup = signup
                account = {"id": 1, "email": "user@example.com", "admin": True}
                with patch(
                    "app.states.menu_auth_state.authenticate",
                    new_callable=AsyncMock,
                    return_value=("new", account),
                ):
                    events = await run_handler(
                        MenuAuthState.authenticate_account,
                        auth,
                        "user@example.com",
                        "password",
                    )
                self.assertEqual(auth.token, "new")
                self.assertEqual(auth.email, account["email"])
                self.assertTrue(auth.authenticated)
                self.assertTrue(auth.admin)
                self.assertTrue(auth.ready)
                self.assertFalse(auth.busy)
                self.assertEqual(auth.error, "")
                self.assertEqual(len(events), 2)

    async def test_unexpected_errors_remain_logged_and_visible(self):
        auth = self.auth_context("admin", True)
        state = self.configuration_context(auth)
        error = RuntimeError("unavailable")
        with (
            patch(
                "app.states.menu_configuration_state.read_administration",
                new_callable=AsyncMock,
                side_effect=error,
            ),
            patch("logging.error") as log,
            patch("logging.exception") as exception_log,
        ):
            await run_handler(MenuConfigurationState.load_configuration, state)
        exception_log.assert_called_once_with(f"Error: {error}")
        log.assert_not_called()
        self.assertTrue(state.error)
        self.assertFalse(state.loading)
        self.assertEqual(auth.token, "admin")
        for handler, service, args in (
            (MenuAuthState.restore_session, "resolve_policy", ()),
            (
                MenuAuthState.authenticate_account,
                "authenticate",
                ("user@example.com", "password"),
            ),
        ):
            with self.subTest(service=service):
                auth = self.auth_context("admin", True)
                with (
                    patch(
                        f"app.states.menu_auth_state.{service}",
                        new_callable=AsyncMock,
                        side_effect=RuntimeError("unavailable"),
                    ),
                    patch("logging.error") as log,
                    patch("logging.exception") as exception_log,
                ):
                    await run_handler(handler, auth, *args)
                log.assert_called_once()
                logged_error = log.call_args.kwargs["exc_info"][1]
                self.assertEqual(
                    log.call_args.kwargs["exc_info"],
                    (
                        type(logged_error),
                        logged_error,
                        logged_error.__traceback__,
                    ),
                )
                exception_log.assert_not_called()
                self.assertTrue(auth.error)

        state = self.configuration_context(self.auth_context("admin", True))
        with (
            patch(
                "app.states.menu_configuration_state.edit_policy",
                new_callable=AsyncMock,
                side_effect=error,
            ),
            patch("logging.error") as log,
            patch("logging.exception") as exception_log,
        ):
            events = await run_handler(
                MenuConfigurationState.save_edit, state, "agricole", "toggle"
            )
        log.assert_called_once_with(
            f"Error: {error}",
            exc_info=(type(error), error, error.__traceback__),
        )
        exception_log.assert_not_called()
        self.assertTrue(state.error)
        self.assertFalse(state.saving)
        self.assertEqual(len(events), 1)


if __name__ == "__main__":
    unittest.main()

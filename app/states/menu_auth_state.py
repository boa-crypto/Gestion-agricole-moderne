import reflex as rx

import asyncio
import logging
import time
from typing import Any

from app.menu_service import (
    SESSION_SECONDS,
    authenticate,
    resolve_account,
    revoke_session,
)


class MenuAuthState(rx.State):
    token: str = rx.Cookie(
        "",
        name="agripro_menu_session",
        path="/",
        max_age=SESSION_SECONDS,
        same_site="strict",
        secure=True,
    )
    email: str = ""
    authenticated: bool = False
    admin: bool = False
    ready: bool = False
    busy: bool = False
    signup: bool = False
    error: str = ""
    _next_attempt: float = 0.0

    @rx.event
    def change_mode(self):
        self.signup = not self.signup
        self.error = ""

    @rx.event(background=True)
    async def restore_session(self):
        async with self:
            token = self.token
            self.ready = False
        if token:
            (result,) = await asyncio.gather(
                resolve_account(token), return_exceptions=True
            )
        else:
            result = {"id": 0, "email": "", "admin": False}
        expired = isinstance(result, PermissionError)
        if isinstance(result, Exception):
            account = {"id": 0, "email": "", "admin": False}
            if not expired:
                logging.error(
                    f"Error: {result}",
                    exc_info=(type(result), result, result.__traceback__),
                )
        else:
            account = result
        async with self:
            if self.token != token:
                return
            if expired:
                self.token = ""
                self.error = (
                    "Votre session a expiré. Veuillez vous reconnecter."
                )
            elif isinstance(result, Exception):
                self.error = "La connexion est indisponible. Réessayez."
            self.authenticated = account["id"] > 0
            self.email = account["email"]
            self.admin = account["admin"]
            self.ready = True
        from app.states.menu_configuration_state import MenuConfigurationState

        yield MenuConfigurationState.load_configuration

    @rx.event
    def submit(self, form_data: dict[str, Any]):
        if self.busy or time.monotonic() < self._next_attempt:
            return rx.toast("Veuillez patienter avant de réessayer.")
        self.busy = True
        self.error = ""
        self._next_attempt = time.monotonic() + 3
        return MenuAuthState.authenticate_account(
            str(form_data.get("email", "")), str(form_data.get("password", ""))
        )

    @rx.event(background=True)
    async def authenticate_account(self, email: str, password: str):
        async with self:
            signup = self.signup
            old_token = self.token
        (result,) = await asyncio.gather(
            authenticate(email, password, signup, old_token),
            return_exceptions=True,
        )
        if isinstance(result, (ValueError, PermissionError)):
            async with self:
                self.error = str(result)
        elif isinstance(result, Exception):
            logging.error(
                f"Error: {result}",
                exc_info=(type(result), result, result.__traceback__),
            )
            async with self:
                self.error = "Connexion indisponible. Veuillez réessayer."
        else:
            token, account = result
            async with self:
                self.token = token
                self.email = account["email"]
                self.authenticated = True
                self.admin = account["admin"]
                self.ready = True
                self.error = ""
            from app.states.menu_configuration_state import (
                MenuConfigurationState,
            )

            yield MenuConfigurationState.load_configuration
            yield rx.toast("Compte créé." if signup else "Connexion réussie.")
        async with self:
            self.busy = False

    @rx.event(background=True)
    async def logout(self):
        async with self:
            token = self.token
            self.busy = True
        try:
            await revoke_session(token)
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "La déconnexion a échoué. Réessayez pour révoquer la session."
            yield rx.toast("Déconnexion impossible ; veuillez réessayer.")
        else:
            async with self:
                self.token = ""
                self.authenticated = False
                self.admin = False
                self.email = ""
            from app.states.menu_configuration_state import (
                MenuConfigurationState,
            )

            yield MenuConfigurationState.load_configuration
            yield rx.toast("Session révoquée. Vous êtes déconnecté.")
        finally:
            async with self:
                self.busy = False

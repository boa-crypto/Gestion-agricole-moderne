import reflex as rx

import asyncio
import logging
import time
from typing import Any

from app.auth_dispatch import PAGE_LOADERS, loader_key, safe_destination
from app.navigation import ROUTE_MATRIX
from app.menu_policy import resolve_policy
from app.menu_service import (
    SESSION_SECONDS,
    authenticate,
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
    permissions: list[str] = []
    allowed_crm_tabs: list[str] = []
    has_modules: bool = False
    page_allowed: bool = False
    requested_entry: str = "global.overview"
    busy: bool = False
    signup: bool = False
    error: str = ""
    _next_attempt: float = 0.0
    return_path: str = "/"
    verified_path: str = ""
    _verified_token: str = ""
    _generation: int = 0
    _dispatch_page: str = ""
    _dispatch_index: int = 0
    _pending_loader: str = ""

    @rx.event(background=True)
    async def verify_page(self, page: str, generation: int):
        from app.states.navigation_state import NavigationState

        async with self:
            if generation != self._generation or page not in ROUTE_MATRIX:
                return
            token = self.token
        if token:
            (result,) = await asyncio.gather(
                resolve_policy(token), return_exceptions=True
            )
        else:
            result = PermissionError("Connexion requise.")
        if not isinstance(result, Exception) and not result.get("active", True):
            result = PermissionError("Compte désactivé.")
        if isinstance(result, Exception) and not isinstance(
            result, PermissionError
        ):
            logging.error(
                "Error: session verification failed",
                exc_info=(type(result), result, result.__traceback__),
            )
        async with self:
            if generation != self._generation or token != self.token:
                return
            self.ready = True
            nav = await self.get_state(NavigationState)
            self.permissions = []
            self.allowed_crm_tabs = []
            self.has_modules = False
            self.page_allowed = False
            nav.cockpits = []
            nav.visible_navigation = []
            if isinstance(result, Exception):
                from app.server_guard import clear_session_views

                await clear_session_views(
                    self,
                    clear_token=isinstance(result, PermissionError),
                    auth_state=self,
                )
                self.authenticated = False
                self.admin = False
                self.email = ""
                self.verified_path = ""
                self._verified_token = ""
                if isinstance(result, PermissionError):
                    self.token = ""
                    if token:
                        self.error = (
                            "Votre session a expiré. Veuillez vous reconnecter."
                        )
                else:
                    self.error = "La connexion est indisponible. Réessayez."
            else:
                nav._apply_policy(result)
                self.permissions = result["permissions"]
                self.allowed_crm_tabs = result["crm_tabs"]
                self.has_modules = bool(result["navigation"])
                self.page_allowed = any(
                    entry["key"] == self.requested_entry
                    for entry in result["navigation"]
                )
                self.authenticated = True
                self.email = result["email"]
                self.admin = result["admin"]
                self._verified_token = token
                self.verified_path = ROUTE_MATRIX[page]["route"]
                self.error = ""
            if isinstance(result, Exception) or not self.admin:
                from app.states.menu_configuration_state import (
                    MenuConfigurationState,
                )

                config = await self.get_state(MenuConfigurationState)
                config._clear_sensitive()
        if isinstance(result, Exception):
            if isinstance(result, PermissionError) and page != "cockpit":
                yield rx.redirect("/")
            return
        if self.page_allowed:
            yield MenuAuthState.dispatch_loader(page, 0, generation)

    @rx.event(background=True)
    async def dispatch_loader(self, page: str, index: int, generation: int):
        from app.states.navigation_state import NavigationState

        async with self:
            if (
                generation != self._generation
                or not self.authenticated
                or page not in PAGE_LOADERS
            ):
                return
            token = self.token
        (result,) = await asyncio.gather(
            resolve_policy(token), return_exceptions=True
        )
        async with self:
            if generation != self._generation or token != self.token:
                return
            if isinstance(result, Exception):
                self.authenticated = False
                self.admin = False
                self.email = ""
                self.verified_path = ""
                self._verified_token = ""
                self._pending_loader = ""
                self.permissions = []
                self.allowed_crm_tabs = []
                self.page_allowed = False
                self.has_modules = False
                nav = await self.get_state(NavigationState)
                nav.cockpits = []
                nav.visible_navigation = []
                self.error = "Session expirée ou vérification indisponible. Reconnectez-vous."
                if isinstance(result, PermissionError):
                    self.token = ""
                self.ready = True
                from app.states.menu_configuration_state import (
                    MenuConfigurationState,
                )

                config = await self.get_state(MenuConfigurationState)
                config._clear_sensitive()
            else:
                nav = await self.get_state(NavigationState)
                nav._apply_policy(result)
                self.permissions = result["permissions"]
                self.allowed_crm_tabs = result["crm_tabs"]
                self.admin = result["admin"]
                self.has_modules = bool(result["navigation"])
                self.page_allowed = any(
                    entry["key"] == self.requested_entry
                    for entry in result["navigation"]
                )
                if not self.admin:
                    from app.states.menu_configuration_state import (
                        MenuConfigurationState,
                    )

                    config = await self.get_state(MenuConfigurationState)
                    config._clear_sensitive()
                if not self.page_allowed:
                    self._pending_loader = ""
                    return
                self._dispatch_page = page
                self._dispatch_index = index
                handlers = PAGE_LOADERS[page]
                self._pending_loader = (
                    loader_key(handlers[index]) if index < len(handlers) else ""
                )
        if isinstance(result, Exception):
            if not isinstance(result, PermissionError):
                logging.error(
                    "Error: loader session verification failed",
                    exc_info=(type(result), result, result.__traceback__),
                )
            yield rx.redirect("/")
            return
        if index < len(handlers):
            yield handlers[index]

    @rx.event
    async def retry_page(self):
        from app.states.navigation_state import NavigationState

        nav = await self.get_state(NavigationState)
        return NavigationState.enter_page(nav.page_key)

    @rx.event
    def change_mode(self):
        self.signup = not self.signup
        self.error = ""

    @rx.event(background=True)
    async def restore_session(self):
        async with self:
            token = self.token
            self.ready = False
            self.authenticated = False
            self.admin = False
            self.email = ""
            self.verified_path = ""
            self._verified_token = ""
        if token:
            (result,) = await asyncio.gather(
                resolve_policy(token), return_exceptions=True
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
            self._verified_token = token if account["id"] > 0 else ""
            self.authenticated = account["id"] > 0
            self.email = account["email"]
            self.admin = account["admin"]
            self.permissions = account.get("permissions", [])
            self.allowed_crm_tabs = account.get("crm_tabs", [])
            self.has_modules = bool(account.get("navigation", []))
            self.page_allowed = False
            self.ready = True
            if not self.admin:
                from app.states.menu_configuration_state import (
                    MenuConfigurationState,
                )

                config = await self.get_state(MenuConfigurationState)
                config._clear_sensitive()
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
            self.authenticated = False
            self.admin = False
            self.email = ""
            self.verified_path = ""
            self._verified_token = ""
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
                self._verified_token = token
                destination = safe_destination(
                    getattr(self, "return_path", "/")
                )
                self.return_path = "/"
            yield rx.redirect(destination)
            yield rx.toast("Compte créé." if signup else "Connexion réussie.")
        async with self:
            self.busy = False

    @rx.event(background=True)
    async def logout(self):
        async with self:
            token = self.token
            self.busy = True
            self.ready = False
            self.authenticated = False
            self.admin = False
            self.email = ""
            self.verified_path = ""
            self._verified_token = ""
            self._pending_loader = ""
            self.permissions = []
            self.allowed_crm_tabs = []
            self.has_modules = False
            self.page_allowed = False
            self._generation += 1
            from app.states.navigation_state import NavigationState
            from app.states.menu_configuration_state import (
                MenuConfigurationState,
            )

            nav = await self.get_state(NavigationState)
            nav.cockpits = []
            nav.visible_navigation = []
            nav.panel_open = False
            nav.mobile_open = False
            nav.navigation_error = ""
            nav.page_key = "cockpit"
            nav.current_key = "global.overview"
            nav.selected_cockpit = "global"
            config = await self.get_state(MenuConfigurationState)
            config._clear_sensitive()
            config.error = ""
            from app.server_guard import clear_session_views

            await clear_session_views(self, auth_state=self)
            self.ready = False
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
                self.return_path = "/"
                self._dispatch_page = ""
                self._dispatch_index = 0
                self.error = ""
            yield rx.redirect("/")
            yield rx.toast("Session révoquée. Vous êtes déconnecté.")
        finally:
            async with self:
                self.busy = False
                self.ready = True

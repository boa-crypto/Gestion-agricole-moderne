import reflex as rx

import asyncio
import logging

from app.menu_service import (
    MenuRow,
    filter_catalog,
    menu_catalog,
    read_settings,
    toggle_setting,
)


class MenuConfigurationState(rx.State):
    rows: list[MenuRow] = []
    search: str = ""
    status_filter: str = "Tous"
    level_filter: str = "Tous"
    loading: bool = False
    saving: bool = False
    allowed: bool = False
    error: str = ""
    notice: str = ""
    _generation: int = 0

    @rx.var
    def filtered_rows(self) -> list[MenuRow]:
        return filter_catalog(
            self.rows, self.search, self.status_filter, self.level_filter
        )

    @rx.var
    def total(self) -> int:
        return len(self.rows)

    @rx.var
    def active(self) -> int:
        return sum(row["effective"] for row in self.rows)

    @rx.var
    def disabled_count(self) -> int:
        return self.total - self.active

    @rx.event
    def set_search(self, value: str):
        self.search = value

    @rx.event
    def clear_search(self):
        self.search = ""
        return rx.set_focus("menu-search")

    @rx.event
    def set_status_filter(self, value: str):
        if value in ("Tous", "Activés", "Désactivés"):
            self.status_filter = value

    @rx.event
    def set_level_filter(self, value: str):
        if value in ("Tous", "Principaux", "Sous-menus"):
            self.level_filter = value

    @rx.event(background=True)
    async def load_configuration(self):
        from app.states.menu_auth_state import MenuAuthState

        async with self:
            auth = await self.get_state(MenuAuthState)
            token = auth.token
            self._generation += 1
            generation = self._generation
            self.loading = True
            self.allowed = False
            self.rows = []
            self.error = ""
            if not token or (auth.ready and not auth.admin):
                self.loading = False
                return
        (result,) = await asyncio.gather(
            read_settings(token, require_admin=True), return_exceptions=True
        )
        if isinstance(result, Exception) and not isinstance(
            result, PermissionError
        ):
            logging.error(
                f"Error: {result}",
                exc_info=(type(result), result, result.__traceback__),
            )
        async with self:
            auth = await self.get_state(MenuAuthState)
            if generation == self._generation:
                self.loading = False
            if generation != self._generation or token != auth.token:
                return
            if isinstance(result, PermissionError):
                auth.token = ""
                auth.authenticated = False
                auth.admin = False
                auth.email = ""
                auth.ready = True
                auth.error = "Session expirée ou accès administrateur refusé. Reconnectez-vous."
                self.allowed = False
                self.rows = []
            elif isinstance(result, Exception):
                self.error = "Impossible de charger la configuration."
            else:
                self.rows = menu_catalog(result)
                self.allowed = True

    @rx.event
    def toggle_menu(self, key: str):
        if self.saving:
            return
        self.saving = True
        self.notice = ""
        return MenuConfigurationState.save_toggle(key)

    @rx.event(background=True)
    async def save_toggle(self, key: str):
        from app.states.menu_auth_state import MenuAuthState
        from app.states.navigation_state import NavigationState

        async with self:
            auth = await self.get_state(MenuAuthState)
            token = auth.token
        (result,) = await asyncio.gather(
            toggle_setting(token, key), return_exceptions=True
        )
        if isinstance(result, PermissionError):
            async with self:
                self.allowed = False
                self.rows = []
                self.error = "Session expirée ou accès administrateur refusé. Reconnectez-vous."
            yield MenuAuthState.restore_session
            yield rx.toast("Accès refusé. Aucune modification enregistrée.")
        elif isinstance(result, ValueError):
            async with self:
                self.error = str(result)
            yield rx.toast(str(result))
        elif isinstance(result, Exception):
            logging.error(
                f"Error: {result}",
                exc_info=(type(result), result, result.__traceback__),
            )
            async with self:
                self.error = (
                    "Échec de l’enregistrement. Aucune modification confirmée."
                )
            yield rx.toast("Impossible d’enregistrer la modification.")
        else:
            async with self:
                auth = await self.get_state(MenuAuthState)
                if token == auth.token:
                    self.rows = menu_catalog(result)
                    self.notice = (
                        "Modification enregistrée. Navigation mise à jour."
                    )
                    self.error = ""
                    nav = await self.get_state(NavigationState)
                    nav._apply_settings(result)
            yield rx.toast("Modification enregistrée.")
        async with self:
            self.saving = False

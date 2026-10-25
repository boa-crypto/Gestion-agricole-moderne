import reflex as rx

import asyncio
import logging

from app.menu_service import (
    MenuRow,
    filter_catalog,
    menu_catalog,
)
from app.menu_policy_admin import (
    AccountRow,
    AssignmentRow,
    AuditRow,
    PermissionRow,
    RoleRow,
    ConfigurationDenied,
    SessionExpired,
    read_administration,
    edit_policy,
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
    tab: str = "Menus"
    roles: list[RoleRow] = []
    accounts: list[AccountRow] = []
    permissions: list[PermissionRow] = []
    assignments: list[AssignmentRow] = []
    audit: list[AuditRow] = []
    selected_role: str = ""
    selected_account: str = ""
    selected_email: str = ""
    selected_active: bool = False
    active_target: str = ""
    active_explicit: str = "n"
    role_search: str = ""
    role_filter: str = "Tous"
    account_search: str = ""
    account_filter: str = "Tous"
    permission_search: str = ""
    permission_filter: str = "Tous"
    account_offset: int = 0
    account_total: int = 0
    audit_offset: int = 0
    audit_total: int = 0

    def _clear_sensitive(self):
        self._generation += 1
        self.rows = []
        self.roles = []
        self.accounts = []
        self.permissions = []
        self.assignments = []
        self.audit = []
        self.selected_role = ""
        self.selected_account = ""
        self.selected_email = ""
        self.selected_active = False
        self.active_target = ""
        self.active_explicit = "n"
        self.account_total = 0
        self.audit_total = 0
        self.account_offset = 0
        self.audit_offset = 0
        self.allowed = False
        self.notice = ""
        self.search = ""
        self.role_search = ""
        self.account_search = ""
        self.permission_search = ""
        self.loading = False
        self.saving = False

    @rx.var
    def filtered_roles(self) -> list[RoleRow]:
        term = self.role_search.strip().casefold()
        return [
            r
            for r in self.roles
            if (not term or term in f"{r['label']} {r['key']}".casefold())
            and (self.role_filter == "Tous" or r["overrides"] > 0)
        ]

    @rx.var
    def filtered_permissions(self) -> list[PermissionRow]:
        term = self.permission_search.strip().casefold()
        return [
            r
            for r in self.permissions
            if (not term or term in r["key"].casefold())
            and (
                self.permission_filter == "Tous"
                or (self.permission_filter == "Accordés" and r["effective"])
                or (self.permission_filter == "Refusés" and not r["effective"])
                or (
                    self.permission_filter == "Explicites"
                    and r["explicit"] != "n"
                )
            )
        ]

    @rx.event
    def set_tab(self, value: str):
        if value in {"Menus", "Rôles", "Utilisateurs", "Journal"}:
            self.tab = value
            self.selected_role = ""
            self.selected_account = ""
            self.permissions = []
            self.assignments = []
            return MenuConfigurationState.load_configuration

    @rx.event
    def select_role(self, key: str):
        self.selected_role = key
        self.selected_account = ""
        self.permissions = []
        return MenuConfigurationState.load_configuration

    @rx.event
    def select_account(self, key: str):
        self.selected_account = key
        self.selected_role = ""
        self.permissions = []
        self.assignments = []
        return MenuConfigurationState.load_configuration

    @rx.event
    def set_role_search(self, value: str):
        self.role_search = value

    @rx.event
    def set_role_filter(self, value: str):
        if value in {"Tous", "Personnalisés"}:
            self.role_filter = value

    @rx.event
    def set_permission_search(self, value: str):
        self.permission_search = value

    @rx.event
    def set_permission_filter(self, value: str):
        if value in {"Tous", "Accordés", "Refusés", "Explicites"}:
            self.permission_filter = value

    @rx.event
    def set_account_search(self, value: str):
        self.account_search = value
        self.account_offset = 0
        return MenuConfigurationState.load_configuration

    @rx.event
    def set_account_filter(self, value: str):
        if value in {"Tous", "Actifs", "Désactivés", "Administrateurs"}:
            self.account_filter = value
            self.account_offset = 0
            return MenuConfigurationState.load_configuration

    @rx.event
    def account_page(self, direction: int):
        self.account_offset = max(
            0, self.account_offset + (25 if direction > 0 else -25)
        )
        return MenuConfigurationState.load_configuration

    @rx.event
    def journal_page(self, direction: int):
        self.audit_offset = max(
            0, self.audit_offset + (50 if direction > 0 else -50)
        )
        return MenuConfigurationState.load_configuration

    @rx.event
    def edit(self, key: str, mode: str):
        if not self.saving:
            self.saving = True
            self.notice = ""
            return MenuConfigurationState.save_edit(key, mode)

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
            self.error = ""
            role = self.selected_role
            account_id = self.selected_account
            search = self.account_search
            account_filter = self.account_filter
            offset = self.account_offset
            audit_offset = self.audit_offset
        (result,) = await asyncio.gather(
            read_administration(
                token,
                role=role,
                account_id=account_id,
                search=search,
                account_filter=account_filter,
                offset=offset,
                audit_offset=audit_offset,
            ),
            return_exceptions=True,
        )
        if isinstance(
            result, (SessionExpired, ConfigurationDenied, ValueError)
        ):
            async with self:
                auth = await self.get_state(MenuAuthState)
                if generation != self._generation or token != auth.token:
                    return
                self._clear_sensitive()
                self.error = str(result)
                if isinstance(result, SessionExpired):
                    auth.token = ""
                    auth.authenticated = False
                    auth.admin = False
                    auth.email = ""
                    auth.permissions = []
                    auth.allowed_crm_tabs = []
                    auth.page_allowed = False
                    auth.ready = True
                    auth.error = str(result)
                elif isinstance(result, ConfigurationDenied):
                    auth.admin = False
            from app.states.navigation_state import NavigationState

            yield NavigationState.refresh_navigation
            return
        elif isinstance(result, Exception):
            logging.error(
                f"Error: {result}",
                exc_info=(type(result), result, result.__traceback__),
            )
            async with self:
                if generation == self._generation:
                    self._clear_sensitive()
                    self.error = (
                        "Impossible de charger la configuration. Réessayez."
                    )
            return
        else:
            async with self:
                auth = await self.get_state(MenuAuthState)
                if generation != self._generation or token != auth.token:
                    return
                self.loading = False
                self.rows = menu_catalog(result["settings"])
                self.roles = result["roles"]
                self.accounts = result["accounts"]
                self.permissions = result["permissions"]
                self.assignments = result["assignments"]
                self.audit = result["audit"]
                self.selected_email = result["selected_email"]
                self.selected_active = result["selected_active"]
                self.active_target = result["active_target"]
                self.active_explicit = result["active_explicit"]
                self.account_total = result["account_total"]
                self.audit_total = result["audit_total"]
                self.allowed = True

    @rx.event
    def toggle_menu(self, key: str):
        if self.saving:
            return
        self.saving = True
        self.notice = ""
        return MenuConfigurationState.save_edit(key, "toggle")

    @rx.event(background=True)
    async def save_edit(self, key: str, mode: str):
        from app.states.menu_auth_state import MenuAuthState
        from app.states.navigation_state import NavigationState

        async with self:
            auth = await self.get_state(MenuAuthState)
            token = auth.token
        (result,) = await asyncio.gather(
            edit_policy(token, key, mode), return_exceptions=True
        )
        async with self:
            auth = await self.get_state(MenuAuthState)
            if token != auth.token or not auth.authenticated:
                return
        if isinstance(result, PermissionError):
            async with self:
                self._clear_sensitive()
                self.error = str(result)
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
                    self.notice = (
                        "Modification enregistrée. Navigation mise à jour."
                    )
                    self.error = ""
            yield NavigationState.refresh_navigation
            yield MenuConfigurationState.load_configuration
            yield rx.toast("Modification enregistrée.")
        async with self:
            self.saving = False

import reflex as rx
import logging

from app.menu_policy import Policy, resolve_policy

from app.navigation import (
    COCKPIT_BY_KEY,
    ENTRY_BY_KEY,
    NAVIGATION,
    ROUTE_MATRIX,
    Cockpit,
    NavigationEntry,
)


def resolve_navigation_entry(
    page: str, cockpit: str = "", tab: str = ""
) -> NavigationEntry | None:
    """Résout uniquement les destinations existantes, sinon la vue principale."""
    if page not in ROUTE_MATRIX:
        return None
    for entry in NAVIGATION:
        if (
            entry["page"] == page
            and entry["cockpit"] == cockpit
            and COCKPIT_BY_KEY[entry["cockpit"]]["available"]
            and (not tab or entry["tab"] == tab)
        ):
            return entry
    return ROUTE_MATRIX[page]


class NavigationState(rx.State):
    page_key: str = "cockpit"
    selected_cockpit: str = "global"
    current_key: str = "global.overview"
    panel_open: bool = False
    mobile_open: bool = False
    cockpits: list[Cockpit] = []
    visible_navigation: list[NavigationEntry] = []
    navigation_error: str = ""

    def _apply_policy(self, policy: Policy):
        self.cockpits = policy["cockpits"]
        self.visible_navigation = policy["navigation"]
        visible = {entry["key"] for entry in self.visible_navigation}
        if not self.visible_navigation:
            self.current_key = ""
            self.selected_cockpit = ""
            self.panel_open = False
            self.mobile_open = False
            return
        if self.current_key not in visible:
            fallback = self.visible_navigation[0]
            self.current_key = fallback["key"]
            self.selected_cockpit = fallback["cockpit"]
        if self.selected_cockpit not in {item["key"] for item in self.cockpits}:
            self.selected_cockpit = self.visible_navigation[0]["cockpit"]

    @rx.var
    def global_visible(self) -> bool:
        return any(
            entry["key"] == "global.overview"
            for entry in self.visible_navigation
        )

    @rx.var
    def search_visible(self) -> bool:
        return any(
            entry["key"] == "global.search" for entry in self.visible_navigation
        )

    @rx.event(background=True)
    async def refresh_navigation(self):
        try:
            from app.states.menu_auth_state import MenuAuthState

            async with self:
                auth = await self.get_state(MenuAuthState)
                token = auth.token
                generation = auth._generation
                self.cockpits = []
                self.visible_navigation = []
                auth.ready = False
            policy = await resolve_policy(token)
            async with self:
                auth = await self.get_state(MenuAuthState)
                if token != auth.token or generation != auth._generation:
                    return
                self._apply_policy(policy)
                auth.permissions = policy["permissions"]
                auth.allowed_crm_tabs = policy["crm_tabs"]
                auth.admin = policy["admin"]
                auth.has_modules = bool(policy["navigation"])
                auth.page_allowed = any(
                    entry["key"] == auth.requested_entry
                    for entry in policy["navigation"]
                )
                auth.ready = True
                self.navigation_error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                auth = await self.get_state(MenuAuthState)
                if token != auth.token or generation != auth._generation:
                    return
                self.cockpits = []
                self.visible_navigation = []
                auth.permissions = []
                auth.allowed_crm_tabs = []
                auth.page_allowed = False
                auth.has_modules = False
                auth.ready = True
                self.navigation_error = (
                    "Navigation indisponible. Réessayez en changeant de page."
                )

    @rx.var
    def selected_label(self) -> str:
        return COCKPIT_BY_KEY.get(
            self.selected_cockpit, {"label": "Aucun module"}
        )["label"]

    @rx.var
    def selected_note(self) -> str:
        return COCKPIT_BY_KEY.get(
            self.selected_cockpit, {"note": "Aucun module accessible."}
        )["note"]

    @rx.var
    def domains(self) -> list[str]:
        return list(
            dict.fromkeys(
                entry["domain"]
                for entry in self.visible_navigation
                if entry["cockpit"] == self.selected_cockpit
            )
        )

    @rx.var
    def entries(self) -> list[NavigationEntry]:
        return [
            entry
            for entry in self.visible_navigation
            if entry["cockpit"] == self.selected_cockpit
        ]

    @rx.var
    async def current_entry(self) -> NavigationEntry:
        current = ENTRY_BY_KEY.get(
            self.current_key, ROUTE_MATRIX[self.page_key]
        )
        if self.page_key == "crm":
            from app.states.crm_state import CrmState

            crm = await self.get_state(CrmState)
            matches = [
                entry
                for entry in self.visible_navigation
                if entry["page"] == "crm"
                and entry["cockpit"] == current["cockpit"]
                and entry["tab"] == crm.active_tab
            ]
            if matches:
                return matches[0]
        return current

    @rx.var
    async def current_cockpit_label(self) -> str:
        if not self.visible_navigation:
            return "Aucun module"
        entry = await self.current_entry
        return COCKPIT_BY_KEY[entry["cockpit"]]["label"]

    @rx.event
    async def enter_page(self, page: str):
        from app.states.menu_auth_state import MenuAuthState
        from app.auth_dispatch import safe_destination

        if page not in ROUTE_MATRIX:
            return
        auth = await self.get_state(MenuAuthState)
        auth._generation += 1
        generation = auth._generation
        auth.ready = False
        auth.permissions = []
        auth.allowed_crm_tabs = []
        auth.page_allowed = False
        auth.has_modules = False
        auth.authenticated = False
        auth.admin = False
        auth.email = ""
        auth.verified_path = ""
        auth._verified_token = ""
        auth._pending_loader = ""
        self.cockpits = []
        self.visible_navigation = []
        self.navigation_error = ""
        path = ROUTE_MATRIX[page]["route"]
        query_string = self.router.url.query
        fragment = self.router.url.fragment
        destination = f"{path}?{query_string}#{fragment}"
        if page != "cockpit":
            auth.return_path = safe_destination(destination)
        self.page_key = page
        query = self.router.url.query_parameters
        cockpit = str(query.get("cockpit", ""))
        tab = str(query.get("vue", ""))
        entry = resolve_navigation_entry(page, cockpit, tab)
        if entry is None:
            return
        auth.requested_entry = entry["key"]
        self.current_key = entry["key"]
        self.selected_cockpit = entry["cockpit"]
        self.panel_open = False
        self.mobile_open = False
        if page == "crm":
            from app.states.crm_state import CrmState

            crm = await self.get_state(CrmState)
            crm.active_tab = entry["tab"]
        yield MenuAuthState.verify_page(page, generation)

    @rx.event(background=True)
    async def select_crm_tab(self, tab: str):
        from app.states.menu_auth_state import MenuAuthState
        from app.states.crm_state import CrmState

        async with self:
            auth = await self.get_state(MenuAuthState)
            token = auth.token
            generation = auth._generation
            if not auth.authenticated or self.page_key != "crm":
                return
            auth.ready = False
            self.cockpits = []
            self.visible_navigation = []
        try:
            policy = await resolve_policy(token)
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                auth = await self.get_state(MenuAuthState)
                if token == auth.token and generation == auth._generation:
                    auth.page_allowed = False
                    auth.has_modules = False
                    auth.permissions = []
                    auth.allowed_crm_tabs = []
                    auth.ready = True
            return
        async with self:
            auth = await self.get_state(MenuAuthState)
            if token != auth.token or generation != auth._generation:
                return
            self._apply_policy(policy)
            auth.permissions = policy["permissions"]
            auth.allowed_crm_tabs = policy["crm_tabs"]
            auth.has_modules = bool(policy["navigation"])
            auth.admin = policy["admin"]
            auth.ready = True
            auth.page_allowed = tab in policy["crm_tabs"]
            if not auth.page_allowed:
                return
            crm = await self.get_state(CrmState)
            crm.active_tab = tab
            matches = [
                entry
                for entry in policy["navigation"]
                if entry["page"] == "crm" and entry["tab"] == tab
            ]
            if not matches:
                matches = [
                    entry
                    for entry in policy["navigation"]
                    if entry["key"] == "commercial.overview"
                ]
            if matches:
                auth.requested_entry = matches[0]["key"]
                self.current_key = matches[0]["key"]
                self.selected_cockpit = matches[0]["cockpit"]

    @rx.event
    def select_cockpit(self, key: str):
        if key not in {
            item["key"] for item in self.cockpits if item["available"]
        }:
            return
        self.selected_cockpit = key
        self.panel_open = True

    @rx.event
    def close_panel(self):
        self.panel_open = False
        return rx.set_focus("nav-selector")

    @rx.event
    def set_mobile_open(self, opened: bool):
        self.mobile_open = opened

    @rx.event
    def close_mobile(self):
        self.mobile_open = False

    @rx.event
    def toggle_panel(self):
        self.panel_open = not self.panel_open

import reflex as rx
import logging

from app.menu_service import menu_catalog, read_settings

from app.navigation import (
    COCKPITS,
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
    cockpits: list[Cockpit] = COCKPITS
    visible_navigation: list[NavigationEntry] = NAVIGATION
    navigation_error: str = ""

    def _apply_settings(self, overrides: dict[str, bool]):
        visible = {
            row["key"] for row in menu_catalog(overrides) if row["effective"]
        }
        self.cockpits = [
            item
            for item in COCKPITS
            if not item["available"] or item["key"] in visible
        ]
        self.visible_navigation = [
            entry for entry in NAVIGATION if entry["key"] in visible
        ]
        available = {item["key"] for item in self.cockpits if item["available"]}
        if self.current_key not in visible:
            fallback = ENTRY_BY_KEY["configuration.menus"]
            self.current_key = fallback["key"]
            self.selected_cockpit = fallback["cockpit"]
        if self.selected_cockpit not in available:
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
            overrides = await read_settings()
            async with self:
                self._apply_settings(overrides)
                self.navigation_error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self._apply_settings(
                    {row["key"]: False for row in menu_catalog({})}
                )
                self.navigation_error = (
                    "Navigation indisponible. Réessayez en changeant de page."
                )

    @rx.var
    def selected_label(self) -> str:
        return COCKPIT_BY_KEY[self.selected_cockpit]["label"]

    @rx.var
    def selected_note(self) -> str:
        return COCKPIT_BY_KEY[self.selected_cockpit]["note"]

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
        current = ENTRY_BY_KEY[self.current_key]
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
            matches = [
                entry
                for entry in NAVIGATION
                if entry["page"] == "crm" and entry["tab"] == crm.active_tab
            ]
            if matches:
                return matches[0]
        return current

    @rx.var
    async def current_cockpit_label(self) -> str:
        entry = await self.current_entry
        return COCKPIT_BY_KEY[entry["cockpit"]]["label"]

    @rx.event
    async def enter_page(self, page: str):
        if page not in ROUTE_MATRIX:
            return
        self.page_key = page
        query = self.router.url.query_parameters
        cockpit = str(query.get("cockpit", ""))
        tab = str(query.get("vue", ""))
        entry = resolve_navigation_entry(page, cockpit, tab)
        if entry is None:
            return
        self.current_key = entry["key"]
        self.selected_cockpit = entry["cockpit"]
        self.panel_open = False
        self.mobile_open = False
        if page == "crm":
            from app.states.crm_state import CrmState

            crm = await self.get_state(CrmState)
            crm.active_tab = entry["tab"]
        yield NavigationState.refresh_navigation
        from app.states.menu_auth_state import MenuAuthState

        yield MenuAuthState.restore_session

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

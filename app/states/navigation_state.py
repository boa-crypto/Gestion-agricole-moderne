import reflex as rx

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
                for entry in NAVIGATION
                if entry["cockpit"] == self.selected_cockpit
            )
        )

    @rx.var
    def entries(self) -> list[NavigationEntry]:
        return [
            entry
            for entry in NAVIGATION
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
                for entry in NAVIGATION
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

    @rx.event
    def select_cockpit(self, key: str):
        if key not in COCKPIT_BY_KEY or not COCKPIT_BY_KEY[key]["available"]:
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

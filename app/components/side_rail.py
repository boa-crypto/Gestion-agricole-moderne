import reflex as rx

from app.components.guide_help import guide_help_panel
from app.states.help_state import HelpState

_ITEMS: list[tuple[str, str, str, str]] = [
    ("cockpit", "Cockpit", "/", "layout-dashboard"),
    ("parcelles", "Parcelles & cultures", "/parcelles", "map"),
    ("referentiel", "Référentiel cultures", "/referentiel", "sprout"),
    ("phenologie", "Administration phénologie", "/phenologie", "git-branch"),
    ("traitements", "Traitements & récoltes", "/traitements", "spray-can"),
    ("employes", "Employés & compétences", "/employes", "users-round"),
    ("cartographie", "Cartographie", "/cartographie", "map-pinned"),
    ("maintenance", "Engins & maintenance", "/maintenance", "wrench"),
    ("charges", "Charges & dépenses", "/charges", "coins"),
    ("recherche", "Recherche globale", "/recherche", "radar"),
    ("guide", "Guide Agricole", "/guide", "book-open"),
    (
        "administration",
        "Administration & accès",
        "/administration",
        "shield-check",
    ),
    ("audit", "Audit fonctionnel", "/audit", "clipboard-check"),
]

_LINK: dict[bool, str] = {
    True: "group relative flex h-11 w-11 items-center justify-center rounded-2xl border border-lime-300/45 bg-lime-300/15 transition-colors",
    False: "group relative flex h-11 w-11 items-center justify-center rounded-2xl border border-white/[0.06] bg-white/[0.02] hover:border-lime-300/25 hover:bg-white/[0.06] transition-colors",
}

_ICON: dict[bool, str] = {
    True: "h-[1.15rem] w-[1.15rem] stroke-lime-300",
    False: "h-[1.15rem] w-[1.15rem] stroke-emerald-100/45 group-hover:stroke-emerald-50",
}

_MARKER: dict[bool, str] = {
    True: "absolute -left-[9px] top-1/2 -translate-y-1/2 h-5 w-[2px] rounded-full bg-lime-300",
    False: "absolute -left-[9px] top-1/2 -translate-y-1/2 h-5 w-[2px] rounded-full bg-transparent",
}

_MOBILE_LINK: dict[bool, str] = {
    True: "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-lime-300/45 bg-lime-300/15 transition-colors",
    False: "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/[0.06] bg-white/[0.02] transition-colors",
}


def _tooltip(label: str) -> rx.Component:
    return rx.el.span(
        label,
        class_name="pointer-events-none absolute left-[3.4rem] top-1/2 -translate-y-1/2 whitespace-nowrap rounded-lg border border-white/10 bg-[#04140d]/95 px-2.5 py-1.5 text-[11px] font-semibold text-emerald-50/90 opacity-0 translate-x-[-4px] group-hover:opacity-100 group-hover:translate-x-0 group-focus-visible:opacity-100 transition-all duration-150 backdrop-blur-xl z-50",
    )


def _rail_link(label: str, href: str, icon: str, active: bool) -> rx.Component:
    return rx.el.a(
        rx.el.span(class_name=_MARKER[active]),
        rx.icon(icon, class_name=_ICON[active]),
        _tooltip(label),
        href=href,
        title=label,
        aria_label=label,
        class_name=_LINK[active],
    )


def _mobile_link(
    label: str, href: str, icon: str, active: bool
) -> rx.Component:
    return rx.el.a(
        rx.icon(icon, class_name=_ICON[active]),
        href=href,
        title=label,
        aria_label=label,
        class_name=_MOBILE_LINK[active],
    )


def _rail_help_button(active: str) -> rx.Component:
    return rx.el.button(
        rx.icon(
            "life-buoy",
            class_name="h-[1.15rem] w-[1.15rem] stroke-lime-300",
        ),
        _tooltip("Aide contextuelle"),
        type="button",
        title="Aide contextuelle",
        aria_label="Ouvrir l'aide contextuelle",
        on_click=HelpState.toggle_context(active),
        class_name="group relative flex h-11 w-11 items-center justify-center rounded-2xl border border-lime-300/25 bg-lime-300/[0.08] hover:border-lime-300/50 hover:bg-lime-300/[0.16] transition-colors",
    )


def _mobile_help_button(active: str) -> rx.Component:
    return rx.el.button(
        rx.icon(
            "life-buoy",
            class_name="h-[1.15rem] w-[1.15rem] stroke-lime-300",
        ),
        type="button",
        title="Aide contextuelle",
        aria_label="Ouvrir l'aide contextuelle",
        on_click=HelpState.toggle_context(active),
        class_name="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-lime-300/25 bg-lime-300/[0.08] transition-colors",
    )


def _platform_mark() -> rx.Component:
    return rx.el.div(
        rx.el.span(
            "AgriPro",
            class_name="font-['Instrument_Serif'] text-lg leading-none tracking-wide text-emerald-50 sm:text-xl",
        ),
        rx.el.span(
            "Plateforme agricole",
            class_name="hidden text-[8px] font-semibold uppercase tracking-[0.2em] text-lime-300/70 sm:inline",
        ),
        aria_label="Plateforme AgriPro",
        class_name="pointer-events-none fixed right-3 top-2 z-40 flex items-center gap-2 rounded-full border border-lime-300/20 bg-[#04140d]/80 px-3 py-1.5 backdrop-blur-xl md:right-5 md:top-3",
    )


def side_rail(active: str) -> rx.Component:
    return rx.fragment(
        _platform_mark(),
        guide_help_panel(),
        rx.el.nav(
            rx.el.div(
                rx.icon("leaf", class_name="h-4 w-4 stroke-lime-300"),
                title="Domaine végétal",
                class_name="flex h-11 w-11 items-center justify-center rounded-2xl border border-lime-300/20 bg-lime-300/[0.07]",
            ),
            rx.el.div(class_name="h-px w-6 bg-white/10 my-1"),
            *[
                _rail_link(label, href, icon, active == key)
                for key, label, href, icon in _ITEMS
            ],
            rx.el.div(class_name="h-px w-6 bg-white/10 my-1"),
            _rail_help_button(active),
            aria_label="Navigation principale",
            class_name="hidden md:flex fixed left-4 top-1/2 -translate-y-1/2 z-40 flex-col items-center gap-2 rounded-[1.75rem] border border-white/10 bg-[#04120c]/70 px-2.5 py-4 backdrop-blur-xl",
        ),
        rx.el.nav(
            rx.el.div(
                *[
                    _mobile_link(label, href, icon, active == key)
                    for key, label, href, icon in _ITEMS
                ],
                _mobile_help_button(active),
                class_name="flex items-center gap-2 overflow-x-auto",
            ),
            aria_label="Navigation principale",
            class_name="md:hidden fixed bottom-3 left-3 right-3 z-40 rounded-2xl border border-white/10 bg-[#04120c]/85 px-3 py-2.5 backdrop-blur-xl",
        ),
    )

import reflex as rx

from app.states.navigation_state import NavigationState
from app.components.guide_help import guide_help_panel
from app.states.help_state import HelpState


def _cockpit_item(item, compact: bool = False) -> rx.Component:
    return rx.el.button(
        rx.icon(item["icon"], class_name="h-4 w-4 shrink-0"),
        rx.el.span(
            item["label"],
            class_name=rx.cond(
                compact, "hidden xl:block flex-1 text-left", "flex-1 text-left"
            ),
        ),
        rx.cond(
            item["available"],
            rx.icon(
                "chevron-right",
                class_name=rx.cond(
                    compact,
                    "hidden xl:block h-3 w-3 shrink-0",
                    "h-3 w-3 shrink-0",
                ),
            ),
            rx.el.span(
                "À venir",
                class_name=rx.cond(
                    compact,
                    "hidden xl:block text-[9px] text-amber-300 w-fit",
                    "text-[9px] text-amber-300 w-fit",
                ),
            ),
        ),
        type="button",
        disabled=~item["available"],
        title=rx.cond(item["available"], item["label"], item["note"]),
        aria_label=rx.cond(
            item["available"], item["label"], f"{item['label']} — À venir"
        ),
        aria_pressed=NavigationState.selected_cockpit == item["key"],
        on_click=NavigationState.select_cockpit(item["key"]),
        class_name=rx.cond(
            NavigationState.selected_cockpit == item["key"],
            "flex w-full items-center gap-2 rounded-xl border border-lime-300/30 bg-lime-300/10 p-3 text-xs font-semibold text-lime-200 focus-visible:outline-2 focus-visible:outline-lime-300 focus-visible:outline-offset-2 disabled:opacity-45",
            "flex w-full items-center gap-2 rounded-xl border border-transparent bg-transparent p-3 text-xs font-medium text-emerald-100/70 hover:bg-white/5 focus-visible:outline-2 focus-visible:outline-lime-300 focus-visible:outline-offset-2 disabled:opacity-45 disabled:cursor-not-allowed",
        ),
    )


def _context_link(entry) -> rx.Component:
    return rx.el.a(
        rx.icon(entry["icon"], class_name="h-4 w-4 shrink-0 text-lime-300"),
        rx.el.span(entry["label"]),
        href=entry["href"],
        on_click=NavigationState.close_mobile,
        aria_current=rx.cond(
            NavigationState.current_entry["key"] == entry["key"],
            "page",
            "false",
        ),
        class_name=rx.cond(
            NavigationState.current_entry["key"] == entry["key"],
            "flex items-center gap-2 rounded-xl border border-lime-300/30 bg-lime-300/10 p-3 text-xs font-semibold text-lime-200 focus-visible:outline-2 focus-visible:outline-lime-300",
            "flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] p-3 text-xs font-medium text-emerald-50 hover:border-lime-300/40 focus-visible:outline-2 focus-visible:outline-lime-300",
        ),
    )


def _domain(domain) -> rx.Component:
    return rx.el.section(
        rx.el.h3(
            domain,
            class_name="text-[10px] uppercase tracking-[0.16em] font-semibold text-amber-300 mb-2",
        ),
        rx.el.div(
            rx.foreach(
                NavigationState.entries,
                lambda entry: rx.cond(
                    entry["domain"] == domain,
                    _context_link(entry),
                    rx.fragment(),
                ),
            ),
            class_name="flex flex-col gap-2",
        ),
        class_name="min-w-0 w-full",
    )


def _context() -> rx.Component:
    return rx.el.nav(
        rx.el.p(
            NavigationState.selected_note,
            class_name="text-xs text-emerald-100/60 mb-4",
        ),
        rx.el.div(
            rx.foreach(NavigationState.domains, _domain),
            class_name="grid grid-cols-1 sm:grid-cols-2 2xl:grid-cols-3 gap-4 w-full",
        ),
        aria_label=f"Domaines du cockpit {NavigationState.selected_label}",
        class_name="w-full",
    )


def _selector() -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.foreach(
                NavigationState.cockpits,
                lambda item: rx.el.option(
                    rx.cond(
                        item["available"],
                        item["label"],
                        f"{item['label']} — À venir",
                    ),
                    value=item["key"],
                    disabled=~item["available"],
                ),
            ),
            value=NavigationState.selected_cockpit,
            on_change=NavigationState.select_cockpit,
            id="nav-selector",
            aria_label="Sélectionner un cockpit",
            class_name="appearance-none w-full rounded-xl border border-lime-300/25 bg-[#04120c] py-2.5 pl-3 pr-9 text-xs font-semibold text-lime-200 focus-visible:outline-2 focus-visible:outline-lime-300",
        ),
        rx.icon(
            "chevron-down",
            class_name="pointer-events-none absolute right-3 top-3 h-4 w-4 text-lime-300",
        ),
        class_name="relative min-w-0 flex-1 sm:flex-none sm:w-60",
    )


def _mobile_navigation(active: str) -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.trigger(
            rx.el.button(
                rx.icon("menu", class_name="h-5 w-5"),
                type="button",
                aria_label="Ouvrir les cockpits",
                class_name="md:hidden rounded-xl border border-white/10 bg-white/5 p-2.5 text-lime-300 focus-visible:outline-2 focus-visible:outline-lime-300",
            ),
            as_child=True,
        ),
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 z-[70] bg-black/60"
            ),
            rx.radix.primitives.dialog.content(
                rx.el.div(
                    rx.radix.primitives.dialog.title(
                        "Cockpits AgriPro",
                        class_name="font-['Instrument_Serif'] text-2xl text-emerald-50",
                    ),
                    rx.radix.primitives.dialog.close(
                        rx.el.button(
                            rx.icon("x", class_name="h-5 w-5"),
                            type="button",
                            aria_label="Fermer la navigation",
                            class_name="rounded-lg p-2 text-lime-300 focus-visible:outline-2 focus-visible:outline-lime-300",
                        ),
                        as_child=True,
                    ),
                    class_name="flex items-center justify-between gap-3",
                ),
                rx.radix.primitives.dialog.description(
                    "Choisissez un cockpit puis un domaine existant. Échap ferme ce panneau.",
                    class_name="text-xs text-emerald-100/60 mt-2",
                ),
                rx.el.div(
                    rx.foreach(
                        NavigationState.cockpits,
                        lambda item: _cockpit_item(item),
                    ),
                    class_name="flex flex-col gap-1 mt-4",
                ),
                rx.el.div(
                    _context(), class_name="mt-5 border-t border-white/10 pt-4"
                ),
                rx.el.button(
                    "Aide contextuelle",
                    on_click=HelpState.toggle_context(active),
                    class_name="mt-4 rounded-xl border border-lime-300/25 bg-lime-300/10 p-3 text-xs text-lime-200 focus-visible:outline-2 focus-visible:outline-lime-300",
                ),
                class_name="fixed inset-y-3 left-3 right-3 z-[80] overflow-y-auto rounded-3xl border border-lime-300/20 bg-[#04120c] p-5 font-['Inter'] text-emerald-50 focus:outline-hidden",
            ),
        ),
        open=NavigationState.mobile_open,
        on_open_change=NavigationState.set_mobile_open,
    )


def _persistent_link(label: str, href: str, icon: str) -> rx.Component:
    return rx.el.a(
        rx.icon(icon, class_name="h-4 w-4 shrink-0"),
        rx.el.span(label, class_name="hidden xl:inline"),
        href=href,
        title=label,
        aria_label=label,
        class_name="flex items-center gap-2 rounded-xl border border-lime-300/20 bg-lime-300/5 p-3 text-xs font-semibold text-lime-200 focus-visible:outline-2 focus-visible:outline-lime-300",
    )


def side_rail(active: str) -> rx.Component:
    return rx.fragment(
        guide_help_panel(),
        rx.el.aside(
            rx.el.a(
                rx.icon("leaf", class_name="h-5 w-5 text-lime-300 shrink-0"),
                rx.el.span(
                    "AgriPro",
                    class_name="hidden xl:block font-['Instrument_Serif'] text-2xl text-emerald-50",
                ),
                href="/",
                aria_label="AgriPro — cockpit global",
                class_name="flex items-center gap-3 p-3 mb-3 focus-visible:outline-2 focus-visible:outline-lime-300",
            ),
            _persistent_link("Cockpit global", "/", "house"),
            _persistent_link("Recherche globale", "/recherche", "search"),
            rx.el.nav(
                rx.foreach(
                    NavigationState.cockpits,
                    lambda item: _cockpit_item(item, True),
                ),
                aria_label="Cockpits métier",
                class_name="flex flex-col gap-1 flex-1 min-h-0 overflow-y-auto my-3 pr-1",
            ),
            rx.el.button(
                rx.icon("life-buoy", class_name="h-4 w-4"),
                rx.el.span("Aide contextuelle", class_name="hidden xl:block"),
                on_click=HelpState.toggle_context(active),
                aria_label="Ouvrir l'aide contextuelle",
                class_name="flex items-center gap-2 rounded-xl border border-lime-300/25 bg-lime-300/5 p-3 text-xs text-lime-200 shrink-0 focus-visible:outline-2 focus-visible:outline-lime-300",
            ),
            class_name="hidden md:flex fixed inset-y-3 left-3 z-40 w-16 xl:w-64 flex-col rounded-3xl border border-white/10 bg-[#04120c]/90 p-2 xl:p-3 backdrop-blur-xl",
        ),
        rx.el.header(
            rx.el.div(
                _mobile_navigation(active),
                _selector(),
                rx.el.button(
                    rx.icon("panel-top", class_name="h-4 w-4"),
                    rx.el.span("Domaines", class_name="hidden sm:inline"),
                    on_click=NavigationState.toggle_panel,
                    aria_expanded=NavigationState.panel_open,
                    aria_controls="nav-context",
                    title="Ouvrir ou fermer les domaines du cockpit",
                    class_name="rounded-xl border border-white/10 bg-white/5 p-2.5 text-xs text-emerald-50 flex items-center gap-2 focus-visible:outline-2 focus-visible:outline-lime-300",
                ),
                rx.el.a(
                    rx.icon("house", class_name="h-4 w-4"),
                    href="/",
                    title="Cockpit global",
                    aria_label="Cockpit global",
                    class_name="ml-auto rounded-xl border border-white/10 bg-white/5 p-2.5 text-lime-300 focus-visible:outline-2 focus-visible:outline-lime-300",
                ),
                rx.el.a(
                    rx.icon("search", class_name="h-4 w-4"),
                    href="/recherche",
                    title="Recherche globale",
                    aria_label="Recherche globale",
                    class_name="rounded-xl border border-white/10 bg-white/5 p-2.5 text-lime-300 focus-visible:outline-2 focus-visible:outline-lime-300",
                ),
                class_name="flex items-center gap-2 w-full",
            ),
            rx.el.nav(
                rx.el.a(
                    "AgriPro",
                    href="/",
                    class_name="text-lime-300 focus-visible:outline-2 focus-visible:outline-lime-300",
                ),
                rx.icon(
                    "chevron-right", class_name="h-3 w-3 text-emerald-100/40"
                ),
                rx.el.button(
                    NavigationState.current_cockpit_label,
                    on_click=NavigationState.select_cockpit(
                        NavigationState.current_entry["cockpit"]
                    ),
                    class_name="text-emerald-100/70 focus-visible:outline-2 focus-visible:outline-lime-300",
                ),
                rx.icon(
                    "chevron-right", class_name="h-3 w-3 text-emerald-100/40"
                ),
                rx.el.a(
                    NavigationState.current_entry["domain"],
                    href=NavigationState.current_entry["href"],
                    class_name="text-emerald-100/60 focus-visible:outline-2 focus-visible:outline-lime-300",
                ),
                rx.icon(
                    "chevron-right", class_name="h-3 w-3 text-emerald-100/40"
                ),
                rx.el.span(
                    NavigationState.current_entry["label"],
                    aria_current="page",
                    class_name="text-emerald-50",
                ),
                aria_label="Fil d'Ariane",
                class_name="flex flex-wrap items-center gap-2 text-[11px] mt-3",
            ),
            rx.cond(
                NavigationState.panel_open,
                rx.el.div(
                    rx.el.div(
                        rx.el.h2(
                            NavigationState.selected_label,
                            class_name="font-['Instrument_Serif'] text-2xl text-emerald-50",
                        ),
                        rx.el.button(
                            rx.icon("x", class_name="h-4 w-4"),
                            "Fermer",
                            on_click=NavigationState.close_panel,
                            class_name="flex items-center gap-2 rounded-lg p-2 text-xs text-lime-300 focus-visible:outline-2 focus-visible:outline-lime-300",
                        ),
                        class_name="flex items-center justify-between mb-3",
                    ),
                    _context(),
                    id="nav-context",
                    class_name="mt-4 rounded-2xl border border-lime-300/20 bg-[#04120c]/70 p-4",
                ),
                rx.fragment(),
            ),
            class_name="w-full mb-6 rounded-2xl border border-white/10 bg-[#04120c]/65 p-3 sm:p-4 backdrop-blur-xl",
        ),
    )

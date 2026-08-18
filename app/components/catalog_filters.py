"""Navigation par catégories, recherche et filtres cycle / besoin en eau."""

import reflex as rx

from app.states.catalog_browser_state import (
    CatalogBrowserState,
    CategoryNode,
    ChipOption,
)


def _category_chip(node: CategoryNode) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            class_name="h-2 w-2 rounded-full",
            style={"backgroundColor": node["color"]},
        ),
        rx.el.span(node["name"], class_name="truncate"),
        rx.el.span(
            node["varieties"],
            class_name="rounded-full bg-white/10 px-1.5 py-0.5 text-[10px] font-bold text-emerald-100/70",
        ),
        on_click=CatalogBrowserState.select_category(node["key"]),
        title=node["tagline"],
        class_name=rx.cond(
            CatalogBrowserState.category_filter == node["key"],
            "flex items-center gap-2 rounded-full border border-lime-300/45 bg-lime-300/15 px-3 py-1.5 text-xs font-semibold text-lime-100 transition-colors w-fit max-w-full",
            "flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-emerald-100/60 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit max-w-full",
        ),
    )


def _option_chip(
    option: ChipOption, active: rx.Var, handler: rx.event.EventType
) -> rx.Component:
    return rx.el.button(
        rx.icon(option["icon"], class_name="h-3.5 w-3.5"),
        rx.el.span(option["label"]),
        on_click=handler,
        class_name=rx.cond(
            active,
            "flex items-center gap-1.5 rounded-full border border-lime-300/45 bg-lime-300/15 px-3 py-1.5 text-[11px] font-semibold text-lime-100 transition-colors w-fit",
            "flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[11px] font-medium text-emerald-100/55 hover:border-lime-300/25 hover:text-emerald-50 transition-colors w-fit",
        ),
    )


def _cycle_chip(option: ChipOption) -> rx.Component:
    return _option_chip(
        option,
        CatalogBrowserState.cycle_filter == option["value"],
        CatalogBrowserState.set_cycle(option["value"]),
    )


def _water_chip(option: ChipOption) -> rx.Component:
    return _option_chip(
        option,
        CatalogBrowserState.water_filter == option["value"],
        CatalogBrowserState.set_water(option["value"]),
    )


def catalog_filters() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Explorer",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Navigation du référentiel",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "search",
                        class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40",
                    ),
                    rx.el.input(
                        placeholder="Culture, espèce, variété, ravageur, débouché…",
                        default_value=CatalogBrowserState.search_term,
                        on_change=CatalogBrowserState.set_search.debounce(400),
                        class_name="w-full rounded-full border border-white/10 bg-white/[0.04] pl-9 pr-4 py-2 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/35 focus:border-lime-300/40 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors",
                    ),
                    class_name="relative w-full sm:w-80",
                ),
                rx.el.button(
                    rx.icon("eraser", class_name="h-3.5 w-3.5"),
                    rx.el.span("Réinitialiser"),
                    on_click=CatalogBrowserState.reset_filters,
                    class_name=rx.cond(
                        CatalogBrowserState.has_filters,
                        "flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-[11px] font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
                        "hidden",
                    ),
                ),
                class_name="flex flex-wrap items-center gap-2 sm:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4 w-full",
        ),
        rx.el.div(
            rx.el.p(
                "Familles cultivées",
                class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("layers", class_name="h-3.5 w-3.5"),
                    rx.el.span("Toutes les catégories"),
                    on_click=CatalogBrowserState.select_category("TOUS"),
                    class_name=rx.cond(
                        CatalogBrowserState.category_filter == "TOUS",
                        "flex items-center gap-1.5 rounded-full border border-lime-300/45 bg-lime-300/15 px-3 py-1.5 text-xs font-semibold text-lime-100 transition-colors w-fit",
                        "flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-emerald-100/60 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
                    ),
                ),
                rx.foreach(CatalogBrowserState.nodes, _category_chip),
                class_name="flex flex-wrap items-center gap-2 mt-2",
            ),
            class_name="w-full mt-6",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Cycle de la culture",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
                ),
                rx.el.div(
                    rx.foreach(CatalogBrowserState.cycle_chips, _cycle_chip),
                    class_name="flex flex-wrap items-center gap-2 mt-2",
                ),
                class_name="flex-1 min-w-0",
            ),
            rx.el.div(
                rx.el.p(
                    "Besoin en eau",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
                ),
                rx.el.div(
                    rx.foreach(CatalogBrowserState.water_chips, _water_chip),
                    class_name="flex flex-wrap items-center gap-2 mt-2",
                ),
                class_name="flex-1 min-w-0",
            ),
            class_name="flex flex-col lg:flex-row gap-5 w-full mt-5 pt-5 border-t border-white/[0.06]",
        ),
        rx.el.div(
            rx.icon("filter", class_name="h-3.5 w-3.5 text-lime-300/70"),
            rx.el.span(
                CatalogBrowserState.scope_label,
                class_name="text-[11px] font-semibold text-emerald-100/60",
            ),
            rx.el.span("·", class_name="text-emerald-100/30"),
            rx.el.span(
                CatalogBrowserState.result_label,
                class_name="text-[11px] font-semibold text-lime-200",
            ),
            class_name="flex items-center gap-2 w-full mt-5",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )

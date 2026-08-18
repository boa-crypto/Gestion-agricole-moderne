"""Liste des cultures du référentiel, filtrée et sélectionnable."""

import reflex as rx

from app.states.catalog_browser_state import CatalogBrowserState, CultureRow


def _tone_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            (
                "warn",
                "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit",
            ),
            (
                "bad",
                "rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-300 w-fit",
            ),
            (
                "info",
                "rounded-full border border-sky-300/30 bg-sky-300/10 px-2 py-0.5 text-[10px] font-bold text-sky-200 w-fit",
            ),
            "rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/50 w-fit",
        ),
    )


def _culture_button(culture: CultureRow) -> rx.Component:
    return rx.el.button(
        rx.el.div(
            class_name="h-1 w-full rounded-full",
            style={"backgroundColor": culture["color"]},
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(culture["icon"], class_name="h-4 w-4 text-lime-300"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-lime-300/25 bg-lime-300/10",
            ),
            rx.el.div(
                rx.el.p(
                    culture["name"],
                    class_name="text-sm font-semibold text-emerald-50 text-left truncate",
                ),
                rx.el.p(
                    f"{culture['category_name']} · {culture['family']}",
                    class_name="text-[11px] font-medium text-emerald-100/45 text-left truncate mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 w-full mt-3",
        ),
        rx.el.div(
            _tone_badge(culture["cycle_tone"], culture["cycle_label"]),
            _tone_badge(culture["water_tone"], culture["water_short"]),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        rx.el.div(
            rx.el.span(
                f"{culture['species_count']} espèce(s)",
                class_name="text-[10px] font-semibold text-emerald-100/50",
            ),
            rx.el.span("·", class_name="text-emerald-100/25 text-[10px]"),
            rx.el.span(
                f"{culture['variety_count']} variété(s)",
                class_name="text-[10px] font-semibold text-emerald-100/50",
            ),
            rx.el.span(
                f"{culture['yield_max']:.1f} t/ha",
                class_name="text-[10px] font-bold text-amber-200 ml-auto",
            ),
            class_name="flex items-center gap-1.5 w-full mt-3 pt-3 border-t border-white/5",
        ),
        on_click=CatalogBrowserState.select_culture(culture["key"]),
        key=culture["key"],
        class_name=rx.cond(
            CatalogBrowserState.selected_culture == culture["key"],
            "w-full rounded-2xl border border-lime-300/40 bg-lime-300/[0.07] p-4 text-left ring-2 ring-lime-300/25 transition-all",
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left hover:border-lime-300/25 hover:bg-white/[0.05] transition-all",
        ),
    )


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.foreach(
            [0, 1, 2, 3, 4],
            lambda _i: rx.el.div(
                class_name="animate-pulse h-36 rounded-2xl bg-white/[0.05]"
            ),
        ),
        class_name="flex flex-col gap-3",
    )


def _empty() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("search-x", class_name="h-5 w-5 text-amber-200"),
            class_name="flex h-11 w-11 items-center justify-center rounded-2xl border border-amber-300/25 bg-amber-300/10",
        ),
        rx.el.p(
            "Aucune culture pour ces critères",
            class_name="text-sm font-semibold text-emerald-50 mt-3",
        ),
        rx.el.p(
            "Élargissez la recherche, ou levez les filtres de cycle et de "
            "besoin en eau pour retrouver toutes les familles cultivées.",
            class_name="text-[11px] font-medium text-emerald-100/50 mt-1.5",
        ),
        rx.el.button(
            rx.icon("eraser", class_name="h-3.5 w-3.5 text-[#04140d]"),
            rx.el.span(
                "Réinitialiser les filtres", class_name="text-[#04140d]"
            ),
            on_click=CatalogBrowserState.reset_filters,
            class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-xs font-semibold hover:bg-lime-200 transition-colors w-fit mt-4",
        ),
        class_name="flex flex-col items-start rounded-2xl border border-white/10 bg-white/[0.02] p-5",
    )


def catalog_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Cultures",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Familles cultivées",
                    class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.cond(
                CatalogBrowserState.is_filtering,
                rx.icon(
                    "loader-circle",
                    class_name="h-4 w-4 animate-spin text-lime-300",
                ),
                rx.el.span(
                    CatalogBrowserState.cultures.length(),
                    class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] font-bold text-emerald-100/60 w-fit",
                ),
            ),
            class_name="flex items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            CatalogBrowserState.is_loading,
            _skeleton(),
            rx.cond(
                CatalogBrowserState.has_cultures,
                rx.el.div(
                    rx.foreach(CatalogBrowserState.cultures, _culture_button),
                    class_name="flex flex-col gap-3 max-h-[46rem] overflow-y-auto pr-1",
                ),
                _empty(),
            ),
        ),
        class_name="w-full xl:w-[24rem] shrink-0 flex flex-col gap-4 rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl",
    )

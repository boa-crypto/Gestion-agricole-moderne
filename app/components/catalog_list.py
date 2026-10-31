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
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit",
            ),
            (
                "bad",
                "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit",
            ),
            (
                "info",
                "rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10 px-2 py-0.5 text-[10px] font-bold text-[#c3daff] w-fit",
            ),
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/50 w-fit",
        ),
    )


def _culture_button(culture: CultureRow) -> rx.Component:
    return rx.el.button(
        rx.el.div(
            class_name="h-1 w-full rounded-none",
            style={"backgroundColor": culture["color"]},
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(culture["icon"], class_name="h-4 w-4 text-[#d8fa5e]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
            ),
            rx.el.div(
                rx.el.p(
                    culture["name"],
                    class_name="text-sm font-semibold text-[#f2efe4] text-left truncate",
                ),
                rx.el.p(
                    f"{culture['category_name']} · {culture['family']}",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/45 text-left truncate mt-0.5",
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
                class_name="text-[10px] font-semibold text-[#c9c5b4]/50",
            ),
            rx.el.span("·", class_name="text-[#c9c5b4]/25 text-[10px]"),
            rx.el.span(
                f"{culture['variety_count']} variété(s)",
                class_name="text-[10px] font-semibold text-[#c9c5b4]/50",
            ),
            rx.el.span(
                f"{culture['yield_max']:.1f} t/ha",
                class_name="text-[10px] font-bold text-[#ffb894] ml-auto",
            ),
            class_name="flex items-center gap-1.5 w-full mt-3 pt-3 border-t border-[#f2efe4]/8",
        ),
        on_click=CatalogBrowserState.select_culture(culture["key"]),
        key=culture["key"],
        class_name=rx.cond(
            CatalogBrowserState.selected_culture == culture["key"],
            "w-full rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/[0.07] p-4 text-left ring-2 ring-[#d8fa5e]/25 transition-all",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 text-left hover:border-[#d8fa5e]/25 hover:bg-[#16190f] transition-all",
        ),
    )


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.foreach(
            [0, 1, 2, 3, 4],
            lambda _i: rx.el.div(
                class_name="animate-pulse h-36 rounded-none bg-[#16190f]"
            ),
        ),
        class_name="flex flex-col gap-3",
    )


def _empty() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("search-x", class_name="h-5 w-5 text-[#ffb894]"),
            class_name="flex h-11 w-11 items-center justify-center rounded-none border border-[#ff8a5b]/25 bg-[#ff8a5b]/10",
        ),
        rx.el.p(
            "Aucune culture pour ces critères",
            class_name="text-sm font-semibold text-[#f2efe4] mt-3",
        ),
        rx.el.p(
            "Élargissez la recherche, ou levez les filtres de cycle et de "
            "besoin en eau pour retrouver toutes les familles cultivées.",
            class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-1.5",
        ),
        rx.el.button(
            rx.icon("eraser", class_name="h-3.5 w-3.5 text-[#0A0A08]"),
            rx.el.span(
                "Réinitialiser les filtres", class_name="text-[#0A0A08]"
            ),
            on_click=CatalogBrowserState.reset_filters,
            class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2 text-xs font-semibold hover:bg-[#e4ff9b] transition-colors w-fit mt-4",
        ),
        class_name="flex flex-col items-start rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] p-5",
    )


def catalog_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Cultures",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Familles cultivées",
                    class_name="ap-serif text-2xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.cond(
                CatalogBrowserState.is_filtering,
                rx.icon(
                    "loader-circle",
                    class_name="h-4 w-4 animate-spin text-[#d8fa5e]",
                ),
                rx.el.span(
                    CatalogBrowserState.cultures.length(),
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-1 text-[11px] font-bold text-[#c9c5b4]/60 w-fit",
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
        class_name="w-full xl:w-[24rem] shrink-0 flex flex-col gap-4 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 ",
    )

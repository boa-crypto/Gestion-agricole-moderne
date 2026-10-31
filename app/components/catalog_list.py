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
                "rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
            ),
            (
                "bad",
                "rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-danger-soft-rgb))] w-fit",
            ),
            (
                "info",
                "rounded-none border border-[rgb(var(--ap-info-rgb)/0.30)] bg-[rgb(var(--ap-info-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-info-soft-rgb))] w-fit",
            ),
            "rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
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
                rx.icon(culture["icon"], class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
            ),
            rx.el.div(
                rx.el.p(
                    culture["name"],
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] text-left truncate",
                ),
                rx.el.p(
                    f"{culture['category_name']} · {culture['family']}",
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] text-left truncate mt-0.5",
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
                class_name="text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            rx.el.span("·", class_name="text-[rgb(var(--ap-paper-muted-rgb)/0.25)] text-[10px]"),
            rx.el.span(
                f"{culture['variety_count']} variété(s)",
                class_name="text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            rx.el.span(
                f"{culture['yield_max']:.1f} t/ha",
                class_name="text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] ml-auto",
            ),
            class_name="flex items-center gap-1.5 w-full mt-3 pt-3 border-t border-[rgb(var(--ap-paper-rgb)/0.12)]",
        ),
        on_click=CatalogBrowserState.select_culture(culture["key"]),
        key=culture["key"],
        class_name=rx.cond(
            CatalogBrowserState.selected_culture == culture["key"],
            "w-full rounded-none border border-[rgb(var(--ap-accent-rgb)/0.40)] bg-[rgb(var(--ap-accent-rgb))]/[0.07] p-4 text-left ring-2 ring-[rgb(var(--ap-accent-rgb)/0.25)] transition-all",
            "border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4 text-left hover:border-t-[rgb(var(--ap-accent-rgb)/0.40)] hover:bg-[rgb(var(--ap-surface-muted-rgb))] transition-all",
        ),
    )


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.foreach(
            [0, 1, 2, 3, 4],
            lambda _i: rx.el.div(
                class_name="ap-skeleton bg-[rgb(var(--ap-surface-high-rgb)/0.70)] h-36 w-full"
            ),
        ),
        class_name="flex flex-col gap-3",
    )


def _empty() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("search-x", class_name="h-5 w-5 text-[rgb(var(--ap-flame-tint-rgb))]"),
            class_name="flex h-11 w-11 items-center justify-center rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.25)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)]",
        ),
        rx.el.p(
            "Aucune culture pour ces critères",
            class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] mt-3",
        ),
        rx.el.p(
            "Élargissez la recherche, ou levez les filtres de cycle et de "
            "besoin en eau pour retrouver toutes les familles cultivées.",
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1.5",
        ),
        rx.el.button(
            rx.icon("eraser", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-ink-rgb))]"),
            rx.el.span(
                "Réinitialiser les filtres", class_name="text-[rgb(var(--ap-ink-rgb))]"
            ),
            on_click=CatalogBrowserState.reset_filters,
            class_name="flex items-center gap-2 rounded-none bg-[rgb(var(--ap-accent-rgb))] px-4 py-2 text-xs font-semibold hover:bg-[rgb(var(--ap-accent-soft-rgb))] transition-colors w-fit mt-4",
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.12)] flex flex-col items-start pt-5",
    )


def catalog_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Cultures",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Familles cultivées",
                    class_name="ap-serif text-2xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.cond(
                CatalogBrowserState.is_filtering,
                rx.icon(
                    "loader-circle",
                    class_name="h-4 w-4 animate-spin text-[rgb(var(--ap-accent-rgb))]",
                ),
                rx.el.span(
                    CatalogBrowserState.cultures.length(),
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2.5 py-1 text-[11px] font-bold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
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
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full xl:w-[24rem] shrink-0 flex flex-col gap-4 pt-5",
    )

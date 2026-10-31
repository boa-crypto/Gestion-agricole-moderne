import reflex as rx

from app.components.design import (
    action_button,
    field,
    input_class,
    stat,
    tag,
)
from app.states.search_state import PeriodChip, SearchState, TypeChip

_TONE_CHIP_ACTIVE: str = (
    "flex items-center gap-2 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.45)]"
    " bg-[rgb(var(--ap-accent-rgb)/0.15)] px-3 py-1.5 text-xs font-semibold text-[rgb(var(--ap-accent-pale-rgb))]"
    " transition-colors w-fit"
)
_TONE_CHIP_IDLE: str = (
    "flex items-center gap-2 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))]"
    " px-3 py-1.5 text-xs font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)]"
    " hover:border-[rgb(var(--ap-accent-rgb)/0.30)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors w-fit"
)


def _stat(label: str, value: rx.Var | str, unit: str) -> rx.Component:
    return stat(label, value, unit)


def _search_bar() -> rx.Component:
    return rx.el.div(
        rx.icon(
            "search",
            class_name=(
                "pointer-events-none absolute left-0 top-1/2 h-5 w-5 "
                "-translate-y-1/2 text-[rgb(var(--ap-accent-rgb))]"
            ),
        ),
        rx.el.input(
            placeholder=(
                "Rechercher une parcelle, une culture, un intrant, "
                "un salarié, un engin, une opération…"
            ),
            default_value=SearchState.term,
            on_change=SearchState.set_term.debounce(450),
            class_name=(
                "w-full border-0 border-b border-[rgb(var(--ap-paper-rgb)/0.30)] bg-transparent "
                "py-4 pl-8 pr-40 text-lg text-[rgb(var(--ap-paper-rgb))] outline-hidden "
                "transition-colors placeholder:text-[rgb(var(--ap-paper-muted-rgb)/0.82)] "
                "focus:border-[rgb(var(--ap-accent-rgb))]"
            ),
        ),
        rx.el.div(
            rx.cond(
                SearchState.is_loading,
                rx.el.div(
                    rx.icon(
                        "loader-circle",
                        class_name="h-3.5 w-3.5 animate-spin text-[rgb(var(--ap-accent-rgb))]",
                    ),
                    rx.el.span(
                        "Balayage…",
                        class_name=(
                            "ap-mono text-[9px] uppercase tracking-[0.18em] "
                            "text-[rgb(var(--ap-accent-rgb))]"
                        ),
                    ),
                    class_name="flex items-center gap-2",
                ),
                tag(f"{SearchState.total_results} résultat(s)", tone="accent"),
            ),
            class_name="absolute right-0 top-1/2 -translate-y-1/2 flex items-center",
        ),
        class_name="relative w-full",
    )


def _period_chip(chip: PeriodChip) -> rx.Component:
    return rx.el.button(
        rx.el.span(chip["label"]),
        on_click=SearchState.set_period(chip["value"]),
        class_name=rx.cond(
            SearchState.period == chip["value"],
            "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.45)] bg-[rgb(var(--ap-flame-soft-rgb)/0.15)] px-3 py-1.5 text-xs font-semibold text-[rgb(var(--ap-warm-100-rgb))] transition-colors w-fit",
            "rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1.5 text-xs font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] hover:border-[rgb(var(--ap-flame-soft-rgb)/0.30)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors w-fit",
        ),
    )


def _date_field(
    label: str,
    icon: str,
    value: rx.Var,
    on_change: rx.event.EventType,
    name: str,
) -> rx.Component:
    return rx.el.div(
        rx.el.span(label, class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]"),
        field(
            rx.el.input(
                type="date",
                name=name,
                default_value=value,
                on_change=on_change,
                class_name=input_class(icon=True),
            ),
            icon=icon,
            class_name="mt-2",
        ),
        class_name="w-full sm:w-52",
    )


def _type_chip(chip: TypeChip) -> rx.Component:
    return rx.el.button(
        rx.icon(
            chip["icon"],
            class_name=rx.cond(
                SearchState.entity_filter == chip["value"],
                "h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb))]",
                "h-3.5 w-3.5 text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
        ),
        rx.el.span(chip["label"]),
        rx.el.span(
            chip["count"],
            class_name=rx.cond(
                chip["count"] > 0,
                "rounded-none bg-[rgb(var(--ap-accent-rgb)/0.20)] px-1.5 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))]",
                "rounded-none bg-[rgb(var(--ap-surface-raised-rgb))] px-1.5 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
            ),
        ),
        on_click=SearchState.set_entity_filter(chip["value"]),
        class_name=rx.cond(
            SearchState.entity_filter == chip["value"],
            _TONE_CHIP_ACTIVE,
            _TONE_CHIP_IDLE,
        ),
    )


def search_console() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            _stat("Résultats", SearchState.total_results, "instances"),
            _stat("Types couverts", SearchState.tables_touched, "tables"),
            _stat("Sections affichées", SearchState.section_count, "blocs"),
            class_name=(
                "ap-stagger grid grid-cols-1 gap-x-8 gap-y-7 sm:grid-cols-2 "
                "xl:grid-cols-3 w-full"
            ),
        ),
        rx.el.div(_search_bar(), class_name="w-full mt-5"),
        rx.el.div(
            _date_field(
                "Date de début",
                "calendar-arrow-down",
                SearchState.start_date,
                SearchState.set_start_date,
                "start_date",
            ),
            _date_field(
                "Date de fin",
                "calendar-arrow-up",
                SearchState.end_date,
                SearchState.set_end_date,
                "end_date",
            ),
            rx.el.div(
                rx.el.span(
                    "Raccourcis de période",
                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                ),
                rx.el.div(
                    rx.foreach(SearchState.period_chips, _period_chip),
                    class_name="flex flex-wrap items-center gap-2 mt-2",
                ),
                class_name="flex-1 min-w-0",
            ),
            action_button(
                "Réinitialiser",
                icon="rotate-ccw",
                tone="outline",
                on_click=SearchState.reset_search,
                class_name="self-end",
            ),
            class_name="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-end gap-4 w-full mt-5",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("filter", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb)/0.80)]"),
                rx.el.span(
                    "Lecture par type d'actif agricole",
                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                rx.foreach(SearchState.chips, _type_chip),
                class_name="flex flex-wrap items-center gap-2 mt-3",
            ),
            class_name="w-full mt-6 border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-5",
        ),
        rx.cond(
            SearchState.error != "",
            rx.el.div(
                rx.icon(
                    "octagon-alert", class_name="h-4 w-4 text-[rgb(var(--ap-danger-soft-rgb))] shrink-0"
                ),
                rx.el.p(
                    SearchState.error,
                    class_name="text-sm font-medium text-[rgb(var(--ap-warm-150-rgb))]",
                ),
                class_name="flex items-center gap-2 rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb))]/[0.08] px-4 py-3 w-full mt-5",
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )

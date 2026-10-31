import reflex as rx

from app.states.search_state import PeriodChip, SearchState, TypeChip

_TONE_CHIP_ACTIVE: str = (
    "flex items-center gap-2 rounded-none border border-[#d8fa5e]/45"
    " bg-[#d8fa5e]/15 px-3 py-1.5 text-xs font-semibold text-[#efffc4]"
    " transition-colors w-fit"
)
_TONE_CHIP_IDLE: str = (
    "flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f]"
    " px-3 py-1.5 text-xs font-medium text-[#c9c5b4]/60"
    " hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit"
)


def _stat(label: str, value: rx.Var | str, unit: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="ap-eyebrow text-[#c9c5b4]/45",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="ap-serif text-2xl leading-none text-[#f2efe4]",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-2",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-3",
    )


def _search_bar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="pointer-events-none absolute -inset-0.5 rounded-none bg-gradient-to-r from-[#d8fa5e]/25 via-[#8fb37a]/10 to-[#ff8a5b]/20 blur-md",
        ),
        rx.el.div(
            rx.icon(
                "search",
                class_name="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-[#d8fa5e] pointer-events-none",
            ),
            rx.el.input(
                placeholder="Rechercher une parcelle, une culture, un intrant, un salarié, un engin, une opération…",
                default_value=SearchState.term,
                on_change=SearchState.set_term.debounce(450),
                class_name="w-full rounded-none border border-[#d8fa5e]/25 bg-[#0D0F09]/90 py-4 pl-12 pr-32 text-sm font-medium text-[#f2efe4] placeholder:text-[#c9c5b4]/30 focus:border-[#d8fa5e]/60 focus:ring-2 focus:ring-[#d8fa5e]/25 outline-hidden transition-colors",
            ),
            rx.cond(
                SearchState.is_loading,
                rx.el.div(
                    rx.icon(
                        "loader-circle",
                        class_name="h-4 w-4 animate-spin text-[#d8fa5e]",
                    ),
                    rx.el.span(
                        "Balayage…",
                        class_name="text-[11px] font-semibold text-[#e4ff9b]",
                    ),
                    class_name="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2",
                ),
                rx.el.span(
                    f"{SearchState.total_results} résultat(s)",
                    class_name="absolute right-4 top-1/2 -translate-y-1/2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/65",
                ),
            ),
            class_name="relative w-full",
        ),
        class_name="relative w-full",
    )


def _period_chip(chip: PeriodChip) -> rx.Component:
    return rx.el.button(
        rx.el.span(chip["label"]),
        on_click=SearchState.set_period(chip["value"]),
        class_name=rx.cond(
            SearchState.period == chip["value"],
            "rounded-none border border-[#ff8a5b]/45 bg-[#ff8a5b]/15 px-3 py-1.5 text-xs font-semibold text-[#ffdccb] transition-colors w-fit",
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1.5 text-xs font-medium text-[#c9c5b4]/60 hover:border-[#ff8a5b]/30 hover:text-[#f2efe4] transition-colors w-fit",
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
        rx.el.span(
            label,
            class_name="ap-eyebrow text-[#c9c5b4]/45",
        ),
        rx.el.div(
            rx.icon(
                icon,
                class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#d8fa5e]/80 pointer-events-none",
            ),
            rx.el.input(
                type="date",
                name=name,
                default_value=value,
                on_change=on_change,
                class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-9 pr-3 text-sm font-medium text-[#f2efe4] focus:border-[#d8fa5e]/50 focus:ring-2 focus:ring-[#d8fa5e]/20 outline-hidden transition-colors",
            ),
            class_name="relative w-full mt-2",
        ),
        class_name="w-full sm:w-52",
    )


def _type_chip(chip: TypeChip) -> rx.Component:
    return rx.el.button(
        rx.icon(
            chip["icon"],
            class_name=rx.cond(
                SearchState.entity_filter == chip["value"],
                "h-3.5 w-3.5 text-[#d8fa5e]",
                "h-3.5 w-3.5 text-[#c9c5b4]/45",
            ),
        ),
        rx.el.span(chip["label"]),
        rx.el.span(
            chip["count"],
            class_name=rx.cond(
                chip["count"] > 0,
                "rounded-none bg-[#d8fa5e]/20 px-1.5 py-0.5 text-[10px] font-bold text-[#e4ff9b]",
                "rounded-none bg-[#14160f] px-1.5 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/35",
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
            _stat("Fenêtre", SearchState.range_label, ""),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 w-full",
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
                    class_name="ap-eyebrow text-[#c9c5b4]/45",
                ),
                rx.el.div(
                    rx.foreach(SearchState.period_chips, _period_chip),
                    class_name="flex flex-wrap items-center gap-2 mt-2",
                ),
                class_name="flex-1 min-w-0",
            ),
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-4 w-4"),
                rx.el.span("Réinitialiser"),
                on_click=SearchState.reset_search,
                class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/70 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit self-end",
            ),
            class_name="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-end gap-4 w-full mt-5",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("filter", class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
                rx.el.span(
                    "Lecture par type d'actif agricole",
                    class_name="ap-eyebrow text-[#c9c5b4]/45",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                rx.foreach(SearchState.chips, _type_chip),
                class_name="flex flex-wrap items-center gap-2 mt-3",
            ),
            class_name="w-full mt-6 border-t border-[#f2efe4]/12 pt-5",
        ),
        rx.cond(
            SearchState.error != "",
            rx.el.div(
                rx.icon(
                    "octagon-alert", class_name="h-4 w-4 text-[#ff9b8c] shrink-0"
                ),
                rx.el.p(
                    SearchState.error,
                    class_name="text-sm font-medium text-[#ffbcb0]",
                ),
                class_name="flex items-center gap-2 rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/[0.08] px-4 py-3 w-full mt-5",
            ),
            rx.fragment(),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

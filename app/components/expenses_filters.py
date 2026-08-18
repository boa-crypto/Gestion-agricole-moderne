import reflex as rx

from app.states.expenses_state import ExpensesState, Option

_INPUT = "w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 outline-hidden transition-colors"
_SELECT = f"{_INPUT} appearance-none cursor-pointer pr-9"


def _select(
    label: str,
    name: str,
    value: rx.Var,
    all_label: str,
    options: rx.Var,
    on_change: rx.event.EventType,
) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
        ),
        rx.el.div(
            rx.el.select(
                rx.el.option(all_label, value="TOUS"),
                rx.foreach(
                    options,
                    lambda opt: rx.el.option(opt["label"], value=opt["value"]),
                ),
                name=name,
                default_value=value,
                key=f"{name}-{ExpensesState.form_key}",
                on_change=on_change,
                class_name=_SELECT,
            ),
            rx.icon(
                "chevron-down",
                class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
            ),
            class_name="relative w-full mt-2",
        ),
        class_name="w-full sm:w-52",
    )


def _date_field(
    label: str,
    icon: str,
    name: str,
    value: rx.Var,
    on_change: rx.event.EventType,
) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
        ),
        rx.el.div(
            rx.icon(
                icon,
                class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
            ),
            rx.el.input(
                type="date",
                name=name,
                default_value=value,
                on_change=on_change,
                class_name=f"{_INPUT} pl-9",
            ),
            class_name="relative w-full mt-2",
        ),
        class_name="w-full sm:w-48",
    )


def _period_chip(chip: Option) -> rx.Component:
    return rx.el.button(
        rx.el.span(chip["label"]),
        on_click=ExpensesState.set_period(chip["value"]),
        class_name=rx.cond(
            ExpensesState.period == chip["value"],
            "rounded-full border border-amber-300/45 bg-amber-300/15 px-3 py-1.5 text-xs font-semibold text-amber-100 transition-colors w-fit",
            "rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-emerald-100/60 hover:border-amber-300/30 hover:text-emerald-50 transition-colors w-fit",
        ),
    )


def expenses_filters() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.icon("filter", class_name="h-3.5 w-3.5 text-lime-300/80"),
                rx.el.span(
                    "Lecture du registre",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-emerald-100/45",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.span(
                ExpensesState.range_label,
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit ml-auto",
            ),
            rx.el.span(
                ExpensesState.scope_label,
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.icon(
                "search",
                class_name="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300 pointer-events-none",
            ),
            rx.el.input(
                placeholder="Rechercher un libellé, un fournisseur, une facture, un type de charge…",
                default_value=ExpensesState.search,
                on_change=ExpensesState.set_search.debounce(450),
                class_name=f"{_INPUT} pl-11 py-3.5",
            ),
            class_name="relative w-full mt-5",
        ),
        rx.el.div(
            _select(
                "Type de charge",
                "type_filter",
                ExpensesState.type_filter,
                "Tous les types",
                ExpensesState.type_options,
                ExpensesState.set_type_filter,
            ),
            _select(
                "Statut",
                "status_filter",
                ExpensesState.status_filter,
                "Tous les statuts",
                ExpensesState.status_options,
                ExpensesState.set_status_filter,
            ),
            _select(
                "Mode de paiement",
                "payment_filter",
                ExpensesState.payment_filter,
                "Tous les modes",
                ExpensesState.payment_options,
                ExpensesState.set_payment_filter,
            ),
            _select(
                "Rattachement",
                "link_filter",
                ExpensesState.link_filter,
                "Tous les rattachements",
                ExpensesState.link_options,
                ExpensesState.set_link_filter,
            ),
            _date_field(
                "Du",
                "calendar-arrow-down",
                "start_date",
                ExpensesState.start_date,
                ExpensesState.set_start_date,
            ),
            _date_field(
                "Au",
                "calendar-arrow-up",
                "end_date",
                ExpensesState.end_date,
                ExpensesState.set_end_date,
            ),
            class_name="flex flex-wrap items-end gap-3 w-full mt-5",
        ),
        rx.el.div(
            rx.el.div(
                rx.foreach(ExpensesState.period_chips, _period_chip),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.el.button(
                rx.icon(
                    "archive",
                    class_name=rx.cond(
                        ExpensesState.include_archived,
                        "h-4 w-4 text-amber-200",
                        "h-4 w-4 text-emerald-100/50",
                    ),
                ),
                rx.el.span(
                    rx.cond(
                        ExpensesState.include_archived,
                        "Archives incluses",
                        "Archives masquées",
                    )
                ),
                on_click=ExpensesState.toggle_archived,
                class_name=rx.cond(
                    ExpensesState.include_archived,
                    "flex items-center gap-2 rounded-full border border-amber-300/40 bg-amber-300/10 px-3 py-1.5 text-xs font-semibold text-amber-100 transition-colors w-fit",
                    "flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-emerald-100/60 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
                ),
            ),
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-4 w-4"),
                rx.el.span("Réinitialiser"),
                on_click=ExpensesState.reset_filters,
                class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full mt-5 border-t border-white/10 pt-5",
        ),
        rx.cond(
            ExpensesState.error != "",
            rx.el.div(
                rx.icon(
                    "octagon-alert", class_name="h-4 w-4 text-red-300 shrink-0"
                ),
                rx.el.p(
                    ExpensesState.error,
                    class_name="text-sm font-medium text-red-200",
                ),
                class_name="flex items-center gap-2 rounded-2xl border border-red-400/30 bg-red-500/[0.08] px-4 py-3 w-full mt-4",
            ),
            rx.fragment(),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )

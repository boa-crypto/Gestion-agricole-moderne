import reflex as rx

from app.components.design import (
    action_button,
    field,
    input_class,
    section_header,
    select_field,
    tag,
)
from app.states.expenses_state import ExpensesState, Option


def _select(
    label: str,
    name: str,
    value: rx.Var,
    all_label: str,
    options: rx.Var,
    on_change: rx.event.EventType,
) -> rx.Component:
    return rx.el.div(
        rx.el.span(label, class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]"),
        select_field(
            rx.el.option(all_label, value="TOUS"),
            rx.foreach(
                options,
                lambda opt: rx.el.option(opt["label"], value=opt["value"]),
            ),
            name=name,
            default_value=value,
            on_change=on_change,
            form_key=ExpensesState.form_key,
            width="w-full mt-2",
        ),
        class_name="w-full sm:w-64",
    )


def _date_field(
    label: str,
    icon: str,
    name: str,
    value: rx.Var,
    on_change: rx.event.EventType,
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
        class_name="w-full sm:w-48",
    )


def _period_chip(chip: Option) -> rx.Component:
    return rx.el.button(
        rx.el.span(chip["label"]),
        on_click=ExpensesState.set_period(chip["value"]),
        type="button",
        class_name=rx.cond(
            ExpensesState.period == chip["value"],
            "ap-mono inline-flex w-fit items-center border border-[rgb(var(--ap-flame-rgb))] "
            "bg-[rgb(var(--ap-flame-rgb)/0.12)] px-2.5 py-1.5 text-[9px] uppercase "
            "tracking-[0.18em] text-[rgb(var(--ap-flame-tint-rgb))] transition-colors",
            "ap-mono inline-flex w-fit items-center border border-[rgb(var(--ap-paper-rgb)/0.18)] "
            "px-2.5 py-1.5 text-[9px] uppercase tracking-[0.18em] "
            "text-[rgb(var(--ap-paper-muted-rgb)/0.78)] transition-colors hover:border-[rgb(var(--ap-paper-rgb)/0.30)] "
            "hover:text-[rgb(var(--ap-paper-rgb))]",
        ),
    )


def expenses_filters() -> rx.Component:
    return rx.el.section(
        section_header(
            "Filtres",
            "Lecture du registre",
            trailing=rx.el.div(
                tag(ExpensesState.range_label, tone="accent"),
                tag(ExpensesState.scope_label),
                class_name="flex flex-wrap items-center gap-2",
            ),
        ),
        field(
            rx.el.input(
                placeholder=(
                    "Rechercher un libellé, un fournisseur, une facture, "
                    "un type de charge…"
                ),
                default_value=ExpensesState.search,
                on_change=ExpensesState.set_search.debounce(450),
                class_name=input_class(icon=True, extra="py-3.5"),
            ),
            icon="search",
            class_name="mt-5",
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
                        "h-3.5 w-3.5 text-[rgb(var(--ap-flame-tint-rgb))]",
                        "h-3.5 w-3.5",
                    ),
                ),
                rx.el.span(
                    rx.cond(
                        ExpensesState.include_archived,
                        "Archives incluses",
                        "Archives masquées",
                    )
                ),
                type="button",
                on_click=ExpensesState.toggle_archived,
                class_name=rx.cond(
                    ExpensesState.include_archived,
                    "ap-mono inline-flex w-fit items-center gap-2 border "
                    "border-[rgb(var(--ap-flame-rgb)/0.45)] bg-[rgb(var(--ap-flame-rgb)/0.10)] px-3 py-2.5 text-[10px] "
                    "uppercase tracking-[0.18em] text-[rgb(var(--ap-flame-tint-rgb))] transition-colors",
                    "ap-mono inline-flex w-fit items-center gap-2 border "
                    "border-[rgb(var(--ap-paper-rgb)/0.18)] px-3 py-2.5 text-[10px] uppercase "
                    "tracking-[0.18em] text-[rgb(var(--ap-paper-muted-rgb)/0.82)] transition-colors "
                    "hover:border-[rgb(var(--ap-paper-rgb)/0.30)] hover:text-[rgb(var(--ap-paper-rgb))]",
                ),
            ),
            action_button(
                "Réinitialiser",
                icon="rotate-ccw",
                tone="ghost",
                on_click=ExpensesState.reset_filters,
                class_name="ml-auto",
            ),
            class_name=(
                "flex flex-wrap items-center gap-3 w-full mt-5 "
                "border-t border-[rgb(var(--ap-paper-rgb)/0.15)] pt-5"
            ),
        ),
        rx.cond(
            ExpensesState.error != "",
            rx.el.div(
                rx.icon(
                    "octagon-alert", class_name="h-4 w-4 text-[rgb(var(--ap-danger-soft-rgb))] shrink-0"
                ),
                rx.el.p(
                    ExpensesState.error,
                    class_name="text-sm font-medium text-[rgb(var(--ap-warm-150-rgb))]",
                ),
                class_name=(
                    "flex items-center gap-2 border border-[rgb(var(--ap-danger-rgb)/0.30)] "
                    "bg-[rgb(var(--ap-flame-strong-rgb))]/[0.08] px-4 py-3 w-full mt-4"
                ),
            ),
            rx.fragment(),
        ),
        class_name="w-full",
    )

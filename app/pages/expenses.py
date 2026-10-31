import reflex as rx

from app.components.design import meta_ledger, meta_row, page_hero, refresh_button
from app.components.expense_types_panel import expense_types_panel
from app.components.expenses_filters import expenses_filters
from app.components.expenses_forms import expense_form_dialog, type_form_dialog
from app.components.expenses_kpis import expenses_kpis
from app.components.expenses_summary import expenses_summary
from app.components.expenses_table import expenses_table
from app.components.guide_help import help_button
from app.components.shell import app_shell
from app.states.expenses_state import ExpensesState


def _space_header() -> rx.Component:
    return page_hero(
        "Registre financier",
        "Charges & dépenses",
        "Toutes les charges de l'exploitation, rattachées à leurs parcelles, cultures, salariés, engins, chantiers et opérations d'atelier.",
        meta=meta_ledger(
            meta_row("Jour", ExpensesState.today_label),
            meta_row("Reste à régler", f"{ExpensesState.kpis['pending']:.0f} €", tone="flame"),
        ),
        actions=rx.el.div(
            help_button("charges", "Guide des charges"),
            refresh_button(
                on_click=ExpensesState.load_expenses,
                loading=ExpensesState.is_loading,
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
    )


def expenses_page() -> rx.Component:
    return app_shell(
        rx.el.div(
            _space_header(),
            rx.el.div(
                expenses_kpis(),
                expenses_filters(),
                expenses_summary(),
                expenses_table(),
                expense_types_panel(),
                class_name="flex flex-col gap-4 w-full mt-8",
            ),
            expense_form_dialog(),
            type_form_dialog(),
            class_name="flex w-full flex-col gap-6",
        ),
        "charges",
    )

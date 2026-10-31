import reflex as rx

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
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("coins", class_name="h-4 w-4 text-[#d8fa5e]"),
                    rx.el.span(
                        "Registre financier",
                        class_name="ap-eyebrow text-[#D8FA5E]",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Charges & dépenses",
                    class_name="ap-display text-[clamp(2.4rem,4.6vw,4.1rem)] text-[#f2efe4] mt-3",
                ),
                rx.el.p(
                    "Toutes les charges de l'exploitation, rattachées à leurs parcelles, cultures, salariés, engins, chantiers et opérations d'atelier.",
                    class_name="mt-4 text-[13px] leading-relaxed text-[#C9C5B4]/70 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "calendar-days", class_name="h-3.5 w-3.5 text-[#d8fa5e]"
                    ),
                    rx.el.span(
                        ExpensesState.today_label,
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                rx.el.div(
                    rx.icon("wallet", class_name="h-3.5 w-3.5 text-[#ff8a5b]"),
                    rx.el.span(
                        f"{ExpensesState.kpis['pending']:.0f} € restant à régler",
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                help_button("charges", "Guide des charges"),
                rx.el.button(
                    rx.cond(
                        ExpensesState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#0A0A08]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#0A0A08]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#0A0A08]"),
                    on_click=ExpensesState.load_expenses,
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B]",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-[#F2EFE4]/12 pb-8",
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

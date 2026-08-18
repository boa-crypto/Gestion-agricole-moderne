import reflex as rx

from app.states.expenses_state import ExpenseRow, ExpensesState


def _head(label: str, extra: str = "") -> rx.Component:
    return rx.el.th(
        label,
        class_name=f"px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-100/45 whitespace-nowrap {extra}",
    )


def _status_badge(row: ExpenseRow) -> rx.Component:
    return rx.el.span(
        row["status_label"],
        class_name=rx.match(
            row["status_tone"],
            (
                "good",
                "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit whitespace-nowrap",
            ),
            (
                "bad",
                "rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-300 w-fit whitespace-nowrap",
            ),
            "rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/50 w-fit whitespace-nowrap",
        ),
    )


def _icon_button(
    icon: str, title: str, on_click: rx.event.EventType, tone: str
) -> rx.Component:
    return rx.el.button(
        rx.icon(icon, class_name="h-3.5 w-3.5"),
        on_click=on_click,
        title=title,
        class_name=tone,
    )


def _row(row: ExpenseRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.el.div(
                    class_name="h-8 w-1 rounded-full shrink-0",
                    style={"backgroundColor": row["type_color"]},
                ),
                rx.el.div(
                    rx.el.p(
                        row["label"],
                        class_name="text-xs font-semibold text-emerald-50 truncate",
                    ),
                    rx.el.p(
                        f"{row['supplier']} · réf. {row['reference']}",
                        class_name="text-[10px] font-medium text-emerald-100/40 truncate",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-center gap-2.5 min-w-0",
            ),
            class_name="px-3 py-2.5 align-middle min-w-[17rem]",
        ),
        rx.el.td(
            rx.el.div(
                rx.icon(
                    row["type_icon"], class_name="h-3.5 w-3.5 text-lime-300/80"
                ),
                rx.el.span(
                    row["type_name"],
                    class_name="text-[11px] font-semibold text-emerald-100/70 truncate",
                ),
                class_name="flex items-center gap-1.5 min-w-0",
            ),
            class_name="px-3 py-2.5 align-middle min-w-[11rem]",
        ),
        rx.el.td(
            rx.el.div(
                rx.icon(
                    row["link_icon"],
                    class_name="h-3.5 w-3.5 text-emerald-300/70",
                ),
                rx.el.div(
                    rx.el.p(
                        row["link_label"],
                        class_name="text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-100/40",
                    ),
                    rx.el.p(
                        row["link_target"],
                        class_name="text-[11px] font-medium text-emerald-100/65 truncate",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-center gap-1.5 min-w-0",
            ),
            class_name="px-3 py-2.5 align-middle min-w-[12rem]",
        ),
        rx.el.td(
            rx.el.p(
                row["date_label"],
                class_name="text-[11px] font-medium text-emerald-100/65 whitespace-nowrap",
            ),
            rx.el.p(
                f"échéance {row['due_label']}",
                class_name="text-[10px] font-medium text-emerald-100/35 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.p(
                f"{row['amount_ttc']:.2f} €",
                class_name="text-xs font-bold text-lime-200 whitespace-nowrap",
            ),
            rx.el.p(
                f"{row['amount_ht']:.2f} € HT · TVA {row['vat_rate']:.1f} %",
                class_name="text-[10px] font-medium text-emerald-100/35 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle text-right",
        ),
        rx.el.td(
            rx.el.div(
                _status_badge(row),
                rx.cond(
                    row["is_archived"],
                    rx.el.span(
                        "Archivée",
                        class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/45 w-fit whitespace-nowrap",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-1.5",
            ),
            rx.el.p(
                row["payment_label"],
                class_name="text-[10px] font-medium text-emerald-100/40 mt-1 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.div(
                _icon_button(
                    "pencil",
                    "Modifier la dépense",
                    ExpensesState.open_expense_edit(row["id"]),
                    "flex h-7 w-7 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors",
                ),
                rx.cond(
                    (row["status"] == "PAYEE") | row["is_cancelled"],
                    rx.fragment(),
                    _icon_button(
                        "banknote",
                        "Marquer comme payée",
                        ExpensesState.mark_paid(row["id"]),
                        "flex h-7 w-7 items-center justify-center rounded-lg border border-lime-300/30 bg-lime-300/10 text-lime-200 hover:bg-lime-300/20 transition-colors",
                    ),
                ),
                rx.cond(
                    row["is_cancelled"],
                    rx.fragment(),
                    _icon_button(
                        "ban",
                        "Annuler la dépense",
                        ExpensesState.cancel_expense(row["id"]),
                        "flex h-7 w-7 items-center justify-center rounded-lg border border-red-400/30 bg-red-500/10 text-red-300 hover:bg-red-500/20 transition-colors",
                    ),
                ),
                rx.cond(
                    row["is_archived"],
                    _icon_button(
                        "archive-restore",
                        "Réintégrer au registre",
                        ExpensesState.restore_expense(row["id"]),
                        "flex h-7 w-7 items-center justify-center rounded-lg border border-emerald-300/30 bg-emerald-300/10 text-emerald-200 hover:bg-emerald-300/20 transition-colors",
                    ),
                    _icon_button(
                        "archive",
                        "Archiver la dépense",
                        ExpensesState.archive_expense(row["id"]),
                        "flex h-7 w-7 items-center justify-center rounded-lg border border-amber-300/30 bg-amber-300/10 text-amber-200 hover:bg-amber-300/20 transition-colors",
                    ),
                ),
                class_name="flex items-center gap-1.5 justify-end",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        key=key,
        class_name=rx.cond(
            row["is_cancelled"],
            "border-b border-white/5 bg-red-500/[0.05] hover:bg-red-500/[0.09] transition-colors",
            "border-b border-white/5 even:bg-white/[0.02] hover:bg-lime-300/[0.05] transition-colors",
        ),
    )


def expenses_table() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Registre des lignes comptables",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Journal des charges",
                    class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{ExpensesState.expense_count} ligne(s) affichée(s)",
                    class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit",
                ),
                rx.el.span(
                    f"{ExpensesState.shown_total:.0f} € TTC cumulés",
                    class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-3 py-1 text-[11px] font-bold text-lime-200 w-fit",
                ),
                rx.el.button(
                    rx.icon("plus", class_name="h-4 w-4 text-[#04140d]"),
                    rx.el.span("Nouvelle dépense", class_name="text-[#04140d]"),
                    on_click=ExpensesState.open_expense_create,
                    class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full pb-5 border-b border-white/10",
        ),
        rx.cond(
            ExpensesState.has_expenses,
            rx.el.div(
                rx.el.div(
                    rx.el.table(
                        rx.el.thead(
                            rx.el.tr(
                                _head("Ligne de charge"),
                                _head("Type"),
                                _head("Rattachement"),
                                _head("Dates"),
                                _head("Montant", "text-right"),
                                _head("Statut"),
                                _head(""),
                                class_name="border-b border-white/10 bg-white/[0.03]",
                            ),
                        ),
                        rx.el.tbody(
                            rx.foreach(
                                ExpensesState.expenses,
                                lambda row: _row(
                                    row, key=row["id"].to_string()
                                ),
                            ),
                        ),
                        class_name="table-auto w-full min-w-[68rem]",
                    ),
                    class_name="overflow-x-auto",
                ),
                class_name="mt-5 w-full rounded-2xl border border-white/10 bg-[#03110b]/60 overflow-hidden",
            ),
            rx.el.div(
                rx.icon("receipt-text", class_name="h-7 w-7 text-amber-300"),
                rx.el.p(
                    "Aucune dépense ne correspond au périmètre sélectionné.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-3 text-center max-w-md",
                ),
                rx.el.button(
                    rx.icon("rotate-ccw", class_name="h-4 w-4"),
                    rx.el.span("Réinitialiser les filtres"),
                    on_click=ExpensesState.reset_filters,
                    class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit mt-5",
                ),
                class_name="flex flex-col items-center justify-center py-16",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )

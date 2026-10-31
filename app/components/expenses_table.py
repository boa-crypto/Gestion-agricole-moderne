import reflex as rx

from app.states.expenses_state import ExpenseRow, ExpensesState


def _head(label: str, extra: str = "") -> rx.Component:
    return rx.el.th(
        label,
        class_name=f"px-3 py-3 text-left ap-eyebrow text-[#c9c5b4]/45 whitespace-nowrap {extra}",
    )


def _status_badge(row: ExpenseRow) -> rx.Component:
    return rx.el.span(
        row["status_label"],
        class_name=rx.match(
            row["status_tone"],
            (
                "good",
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit whitespace-nowrap",
            ),
            (
                "bad",
                "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit whitespace-nowrap",
            ),
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/50 w-fit whitespace-nowrap",
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
                    class_name="h-8 w-1 rounded-none shrink-0",
                    style={"backgroundColor": row["type_color"]},
                ),
                rx.el.div(
                    rx.el.p(
                        row["label"],
                        class_name="text-xs font-semibold text-[#f2efe4] truncate",
                    ),
                    rx.el.p(
                        f"{row['supplier']} · réf. {row['reference']}",
                        class_name="text-[10px] font-medium text-[#c9c5b4]/40 truncate",
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
                    row["type_icon"], class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"
                ),
                rx.el.span(
                    row["type_name"],
                    class_name="text-[11px] font-semibold text-[#c9c5b4]/70 truncate",
                ),
                class_name="flex items-center gap-1.5 min-w-0",
            ),
            class_name="px-3 py-2.5 align-middle min-w-[11rem]",
        ),
        rx.el.td(
            rx.el.div(
                rx.icon(
                    row["link_icon"],
                    class_name="h-3.5 w-3.5 text-[#a9c98b]/70",
                ),
                rx.el.div(
                    rx.el.p(
                        row["link_label"],
                        class_name="ap-eyebrow text-[#c9c5b4]/40",
                    ),
                    rx.el.p(
                        row["link_target"],
                        class_name="text-[11px] font-medium text-[#c9c5b4]/65 truncate",
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
                class_name="text-[11px] font-medium text-[#c9c5b4]/65 whitespace-nowrap",
            ),
            rx.el.p(
                f"échéance {row['due_label']}",
                class_name="text-[10px] font-medium text-[#c9c5b4]/35 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.p(
                f"{row['amount_ttc']:.2f} €",
                class_name="text-xs font-bold text-[#e4ff9b] whitespace-nowrap",
            ),
            rx.el.p(
                f"{row['amount_ht']:.2f} € HT · TVA {row['vat_rate']:.1f} %",
                class_name="text-[10px] font-medium text-[#c9c5b4]/35 whitespace-nowrap",
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
                        class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/45 w-fit whitespace-nowrap",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-1.5",
            ),
            rx.el.p(
                row["payment_label"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/40 mt-1 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.div(
                _icon_button(
                    "pencil",
                    "Modifier la dépense",
                    ExpensesState.open_expense_edit(row["id"]),
                    "flex h-7 w-7 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#14160f] text-[#c9c5b4]/70 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors",
                ),
                rx.cond(
                    (row["status"] == "PAYEE") | row["is_cancelled"],
                    rx.fragment(),
                    _icon_button(
                        "banknote",
                        "Marquer comme payée",
                        ExpensesState.mark_paid(row["id"]),
                        "flex h-7 w-7 items-center justify-center rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 text-[#e4ff9b] hover:bg-[#d8fa5e]/20 transition-colors",
                    ),
                ),
                rx.cond(
                    row["is_cancelled"],
                    rx.fragment(),
                    _icon_button(
                        "ban",
                        "Annuler la dépense",
                        ExpensesState.cancel_expense(row["id"]),
                        "flex h-7 w-7 items-center justify-center rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 text-[#ff9b8c] hover:bg-[#f2452c]/20 transition-colors",
                    ),
                ),
                rx.cond(
                    row["is_archived"],
                    _icon_button(
                        "archive-restore",
                        "Réintégrer au registre",
                        ExpensesState.restore_expense(row["id"]),
                        "flex h-7 w-7 items-center justify-center rounded-none border border-[#a9c98b]/30 bg-[#a9c98b]/10 text-[#b3af9f] hover:bg-[#a9c98b]/20 transition-colors",
                    ),
                    _icon_button(
                        "archive",
                        "Archiver la dépense",
                        ExpensesState.archive_expense(row["id"]),
                        "flex h-7 w-7 items-center justify-center rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 text-[#ffb894] hover:bg-[#ff8a5b]/20 transition-colors",
                    ),
                ),
                class_name="flex items-center gap-1.5 justify-end",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        key=key,
        class_name=rx.cond(
            row["is_cancelled"],
            "border-b border-[#f2efe4]/8 bg-[#f2452c]/[0.05] hover:bg-[#f2452c]/[0.09] transition-colors",
            "border-b border-[#f2efe4]/8 even:bg-[#0d0f09] hover:bg-[#d8fa5e]/[0.05] transition-colors",
        ),
    )


def expenses_table() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Registre des lignes comptables",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Journal des charges",
                    class_name="ap-serif text-2xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{ExpensesState.expense_count} ligne(s) affichée(s)",
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit",
                ),
                rx.el.span(
                    f"{ExpensesState.shown_total:.0f} € TTC cumulés",
                    class_name="rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-3 py-1 text-[11px] font-bold text-[#e4ff9b] w-fit",
                ),
                rx.el.button(
                    rx.icon("plus", class_name="h-4 w-4 text-[#0A0A08]"),
                    rx.el.span("Nouvelle dépense", class_name="text-[#0A0A08]"),
                    on_click=ExpensesState.open_expense_create,
                    class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2.5 text-sm font-semibold hover:bg-[#e4ff9b] transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full pb-5 border-b border-[#f2efe4]/12",
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
                                class_name="border-b border-[#f2efe4]/12 bg-[#101208]",
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
                class_name="mt-5 w-full rounded-none border border-[#f2efe4]/12 bg-[#0D0F09]/60 overflow-hidden",
            ),
            rx.el.div(
                rx.icon("receipt-text", class_name="h-7 w-7 text-[#ff8a5b]"),
                rx.el.p(
                    "Aucune dépense ne correspond au périmètre sélectionné.",
                    class_name="mt-4 text-[13px] leading-relaxed text-[#C9C5B4]/70 text-center max-w-md",
                ),
                rx.el.button(
                    rx.icon("rotate-ccw", class_name="h-4 w-4"),
                    rx.el.span("Réinitialiser les filtres"),
                    on_click=ExpensesState.reset_filters,
                    class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2 text-sm font-semibold text-[#c9c5b4]/70 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit mt-5",
                ),
                class_name="flex flex-col items-center justify-center py-16",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

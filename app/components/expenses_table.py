import reflex as rx

from app.components.design import action_button, empty_state
from app.states.expenses_state import ExpenseRow, ExpensesState


def _head(label: str, extra: str = "") -> rx.Component:
    return rx.el.th(
        label,
        class_name=f"px-3 py-3 text-left ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)] whitespace-nowrap {extra}",
    )


def _status_badge(row: ExpenseRow) -> rx.Component:
    return rx.el.span(
        row["status_label"],
        class_name=rx.match(
            row["status_tone"],
            (
                "good",
                "rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit whitespace-nowrap",
            ),
            (
                "bad",
                "rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-danger-soft-rgb))] w-fit whitespace-nowrap",
            ),
            "rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit whitespace-nowrap",
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
                        class_name="text-xs font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
                    ),
                    rx.el.p(
                        f"{row['supplier']} · réf. {row['reference']}",
                        class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
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
                    row["type_icon"], class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb)/0.80)]"
                ),
                rx.el.span(
                    row["type_name"],
                    class_name="text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)] truncate",
                ),
                class_name="flex items-center gap-1.5 min-w-0",
            ),
            class_name="px-3 py-2.5 align-middle min-w-[11rem]",
        ),
        rx.el.td(
            rx.el.div(
                rx.icon(
                    row["link_icon"],
                    class_name="h-3.5 w-3.5 text-[rgb(var(--ap-sage-rgb)/0.70)]",
                ),
                rx.el.div(
                    rx.el.p(
                        row["link_label"],
                        class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                    ),
                    rx.el.p(
                        row["link_target"],
                        class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
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
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] whitespace-nowrap",
            ),
            rx.el.p(
                f"échéance {row['due_label']}",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.p(
                f"{row['amount_ttc']:.2f} €",
                class_name="text-xs font-bold text-[rgb(var(--ap-accent-soft-rgb))] whitespace-nowrap",
            ),
            rx.el.p(
                f"{row['amount_ht']:.2f} € HT · TVA {row['vat_rate']:.1f} %",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] whitespace-nowrap",
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
                        class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit whitespace-nowrap",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-1.5",
            ),
            rx.el.p(
                row["payment_label"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.div(
                _icon_button(
                    "pencil",
                    "Modifier la dépense",
                    ExpensesState.open_expense_edit(row["id"]),
                    "flex h-7 w-7 items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] text-[rgb(var(--ap-paper-muted-rgb)/0.90)] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors",
                ),
                rx.cond(
                    (row["status"] == "PAYEE") | row["is_cancelled"],
                    rx.fragment(),
                    _icon_button(
                        "banknote",
                        "Marquer comme payée",
                        ExpensesState.mark_paid(row["id"]),
                        "flex h-7 w-7 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] text-[rgb(var(--ap-accent-soft-rgb))] hover:bg-[rgb(var(--ap-accent-rgb)/0.20)] transition-colors",
                    ),
                ),
                rx.cond(
                    row["is_cancelled"],
                    rx.fragment(),
                    _icon_button(
                        "ban",
                        "Annuler la dépense",
                        ExpensesState.cancel_expense(row["id"]),
                        "flex h-7 w-7 items-center justify-center rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] text-[rgb(var(--ap-danger-soft-rgb))] hover:bg-[rgb(var(--ap-flame-strong-rgb)/0.20)] transition-colors",
                    ),
                ),
                rx.cond(
                    row["is_archived"],
                    _icon_button(
                        "archive-restore",
                        "Réintégrer au registre",
                        ExpensesState.restore_expense(row["id"]),
                        "flex h-7 w-7 items-center justify-center rounded-none border border-[rgb(var(--ap-sage-rgb)/0.30)] bg-[rgb(var(--ap-sage-rgb)/0.10)] text-[rgb(var(--ap-paper-soft-rgb))] hover:bg-[rgb(var(--ap-sage-rgb)/0.20)] transition-colors",
                    ),
                    _icon_button(
                        "archive",
                        "Archiver la dépense",
                        ExpensesState.archive_expense(row["id"]),
                        "flex h-7 w-7 items-center justify-center rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] text-[rgb(var(--ap-flame-tint-rgb))] hover:bg-[rgb(var(--ap-flame-soft-rgb)/0.20)] transition-colors",
                    ),
                ),
                class_name="flex items-center gap-1.5 justify-end",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        key=key,
        class_name=rx.cond(
            row["is_cancelled"],
            "border-b border-[rgb(var(--ap-paper-rgb)/0.12)] bg-[rgb(var(--ap-flame-strong-rgb))]/[0.05] hover:bg-[rgb(var(--ap-flame-strong-rgb))]/[0.09] transition-colors",
            "border-b border-[rgb(var(--ap-paper-rgb)/0.12)] even:bg-[rgb(var(--ap-surface-soft-rgb))] hover:bg-[rgb(var(--ap-accent-rgb))]/[0.05] transition-colors",
        ),
    )


def expenses_table() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Registre des lignes comptables",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Journal des charges",
                    class_name="ap-serif text-2xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{ExpensesState.expense_count} ligne(s) affichée(s)",
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
                ),
                rx.el.span(
                    f"{ExpensesState.shown_total:.0f} € TTC cumulés",
                    class_name="rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-3 py-1 text-[11px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
                ),
                rx.el.button(
                    rx.icon("plus", class_name="h-4 w-4 text-[rgb(var(--ap-ink-rgb))]"),
                    rx.el.span("Nouvelle dépense", class_name="text-[rgb(var(--ap-ink-rgb))]"),
                    on_click=ExpensesState.open_expense_create,
                    class_name="flex items-center gap-2 rounded-none bg-[rgb(var(--ap-accent-rgb))] px-4 py-2.5 text-sm font-semibold hover:bg-[rgb(var(--ap-accent-soft-rgb))] transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full pb-5 border-b border-[rgb(var(--ap-paper-rgb)/0.18)]",
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
                                class_name="border-b border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))]",
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
                class_name="mt-5 w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-4",
            ),
            empty_state(
                "receipt-text",
                "Aucune dépense sur ce périmètre",
                "Élargissez la période ou réinitialisez les filtres pour retrouver le journal complet.",
                action=action_button(
                    "Réinitialiser les filtres",
                    icon="rotate-ccw",
                    on_click=ExpensesState.reset_filters,
                    tone="outline",
                ),
                class_name="flex flex-col items-center justify-center py-16",
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )

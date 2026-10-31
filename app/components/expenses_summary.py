import reflex as rx

from app.states.expenses_state import ExpensesState, MonthPoint, TypeRow


def _month_bar(point: MonthPoint, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                point["label"],
                class_name="text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)] w-20 shrink-0",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="h-2.5 rounded-none bg-gradient-to-r from-[rgb(var(--ap-sage-soft-rgb))] via-[rgb(var(--ap-accent-rgb))] to-[rgb(var(--ap-flame-soft-rgb))]",
                    style={"width": point["width"]},
                ),
                class_name="h-2.5 flex-1 rounded-none bg-[rgb(var(--ap-surface-high-rgb))] min-w-0",
            ),
            rx.el.span(
                f"{point['amount']:.0f} €",
                class_name="text-[11px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-24 text-right shrink-0",
            ),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.span(
            f"{point['count']} ligne(s) comptable(s)",
            class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] ml-[5.75rem]",
        ),
        key=key,
        class_name="w-full",
    )


def _type_line(item: TypeRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(item["icon"], class_name="h-4 w-4 text-[rgb(var(--ap-ink-rgb))]"),
                class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none",
                style={"backgroundColor": item["color"]},
            ),
            rx.el.div(
                rx.el.p(
                    item["name"],
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
                ),
                rx.el.p(
                    f"{item['category']} · {item['expense_count']} ligne(s)",
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                f"{item['total_ttc']:.0f} €",
                class_name="text-xs font-bold text-[rgb(var(--ap-accent-soft-rgb))] shrink-0",
            ),
            class_name="flex items-center gap-3 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-1.5 rounded-none",
                style={
                    "width": item["share"],
                    "backgroundColor": item["color"],
                },
            ),
            class_name="h-1.5 w-full rounded-none bg-[rgb(var(--ap-surface-high-rgb))] mt-2.5",
        ),
        key=key,
        class_name="w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3.5",
    )


def expenses_summary() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Cadence mensuelle des charges",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.span(
                    f"{ExpensesState.kpis['year_total']:.0f} € engagés sur la campagne",
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit ml-auto",
                ),
                class_name="flex flex-wrap items-center gap-3",
            ),
            rx.cond(
                ExpensesState.months.length() > 0,
                rx.el.div(
                    rx.foreach(
                        ExpensesState.months,
                        lambda point: _month_bar(point, key=point["key"]),
                    ),
                    class_name="flex flex-col gap-3.5 mt-5",
                ),
                rx.el.p(
                    "Aucune dépense datée sur les douze derniers mois.",
                    class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-5",
                ),
            ),
            class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] flex-1 min-w-0 pt-6",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Répartition par type",
                    class_name="ap-eyebrow text-[rgb(var(--ap-flame-soft-rgb)/0.80)]",
                ),
                rx.el.span(
                    f"{ExpensesState.type_count} types",
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit ml-auto",
                ),
                class_name="flex flex-wrap items-center gap-3",
            ),
            rx.el.div(
                rx.foreach(
                    ExpensesState.types,
                    lambda item: _type_line(item, key=item["id"].to_string()),
                ),
                class_name="flex flex-col gap-2.5 mt-5 max-h-[26rem] overflow-y-auto pr-1",
            ),
            class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full xl:w-[26rem] shrink-0 pt-6",
        ),
        class_name="flex flex-col xl:flex-row gap-4 w-full",
    )

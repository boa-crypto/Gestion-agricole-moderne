import reflex as rx

from app.states.expenses_state import ExpensesState, MonthPoint, TypeRow


def _month_bar(point: MonthPoint, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                point["label"],
                class_name="text-[11px] font-semibold text-emerald-100/70 w-20 shrink-0",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="h-2.5 rounded-full bg-gradient-to-r from-emerald-400 via-lime-300 to-amber-300",
                    style={"width": point["width"]},
                ),
                class_name="h-2.5 flex-1 rounded-full bg-white/[0.06] min-w-0",
            ),
            rx.el.span(
                f"{point['amount']:.0f} €",
                class_name="text-[11px] font-bold text-lime-200 w-24 text-right shrink-0",
            ),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.span(
            f"{point['count']} ligne(s) comptable(s)",
            class_name="text-[10px] font-medium text-emerald-100/35 ml-[5.75rem]",
        ),
        key=key,
        class_name="w-full",
    )


def _type_line(item: TypeRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(item["icon"], class_name="h-4 w-4 text-[#04140d]"),
                class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl",
                style={"backgroundColor": item["color"]},
            ),
            rx.el.div(
                rx.el.p(
                    item["name"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    f"{item['category']} · {item['expense_count']} ligne(s)",
                    class_name="text-[10px] font-medium text-emerald-100/45 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                f"{item['total_ttc']:.0f} €",
                class_name="text-xs font-bold text-lime-200 shrink-0",
            ),
            class_name="flex items-center gap-3 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-1.5 rounded-full",
                style={
                    "width": item["share"],
                    "backgroundColor": item["color"],
                },
            ),
            class_name="h-1.5 w-full rounded-full bg-white/[0.06] mt-2.5",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-3.5",
    )


def expenses_summary() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Cadence mensuelle des charges",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                rx.el.span(
                    f"{ExpensesState.kpis['year_total']:.0f} € engagés sur la campagne",
                    class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit ml-auto",
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
                    class_name="text-sm font-medium text-emerald-100/50 mt-5",
                ),
            ),
            class_name="flex-1 min-w-0 rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Répartition par type",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-amber-300/80",
                ),
                rx.el.span(
                    f"{ExpensesState.type_count} types",
                    class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit ml-auto",
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
            class_name="w-full xl:w-[26rem] shrink-0 rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
        ),
        class_name="flex flex-col xl:flex-row gap-4 w-full",
    )

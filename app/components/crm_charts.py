import reflex as rx

from app.states.crm_state import AgingPoint, CrmState, MonthPoint


def _legend(color: str, label: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(class_name=color),
        rx.el.span(
            label,
            class_name="text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
        ),
        class_name="flex items-center gap-2 w-fit",
    )


def _month_row(point: MonthPoint, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                point["label"],
                class_name="text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)] w-20 shrink-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        class_name="h-2.5 rounded-none bg-gradient-to-r from-[rgb(var(--ap-sage-soft-rgb))] via-[rgb(var(--ap-accent-rgb))] to-[rgb(var(--ap-accent-soft-rgb))]",
                        style={"width": point["sales_width"]},
                    ),
                    class_name="h-2.5 w-full rounded-none bg-[rgb(var(--ap-surface-high-rgb))]",
                ),
                rx.el.div(
                    rx.el.div(
                        class_name="h-2.5 rounded-none bg-gradient-to-r from-[rgb(var(--ap-warm-400-rgb))] via-[rgb(var(--ap-flame-soft-rgb))] to-[rgb(var(--ap-warm-250-rgb))]",
                        style={"width": point["purchases_width"]},
                    ),
                    class_name="h-2.5 w-full rounded-none bg-[rgb(var(--ap-surface-high-rgb))] mt-1.5",
                ),
                class_name="flex-1 min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{point['sales']:.0f} DA",
                    class_name="text-[11px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] text-right",
                ),
                rx.el.span(
                    f"{point['purchases']:.0f} DA",
                    class_name="text-[11px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] text-right",
                ),
                class_name="flex flex-col w-28 shrink-0",
            ),
            class_name="flex items-center gap-3 w-full",
        ),
        key=key,
        class_name="w-full",
    )


def crm_flow_chart() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Chiffre d'affaires & achats par mois",
                class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
            ),
            rx.el.div(
                _legend(
                    "h-2 w-6 rounded-none bg-gradient-to-r from-[rgb(var(--ap-sage-soft-rgb))] to-[rgb(var(--ap-accent-rgb))]",
                    "Ventes",
                ),
                _legend(
                    "h-2 w-6 rounded-none bg-gradient-to-r from-[rgb(var(--ap-warm-400-rgb))] to-[rgb(var(--ap-warm-250-rgb))]",
                    "Achats",
                ),
                class_name="flex items-center gap-4 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3",
        ),
        rx.cond(
            CrmState.months.length() > 0,
            rx.el.div(
                rx.foreach(
                    CrmState.months,
                    lambda point: _month_row(point, key=point["key"]),
                ),
                class_name="flex flex-col gap-3.5 mt-5",
            ),
            rx.el.p(
                "Aucun flux commercial daté sur les douze derniers mois.",
                class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-5",
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] flex-1 min-w-0 pt-6",
    )


def _aging_row(point: AgingPoint, bar: str, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                point["label"],
                class_name="text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)]",
            ),
            rx.el.span(
                f"{point['amount']:.0f} DA",
                class_name="text-[11px] font-bold text-[rgb(var(--ap-paper-rgb))] ml-auto",
            ),
            class_name="flex items-center gap-2 w-full",
        ),
        rx.el.div(
            rx.el.div(class_name=bar, style={"width": point["width"]}),
            class_name="h-1.5 w-full rounded-none bg-[rgb(var(--ap-surface-high-rgb))] mt-2",
        ),
        rx.el.span(
            f"{point['count']} pièce(s) comptable(s)",
            class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-1.5",
        ),
        key=key,
        class_name="w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3.5 flex flex-col",
    )


def crm_aging_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Balance âgée",
                class_name="ap-eyebrow text-[rgb(var(--ap-flame-soft-rgb)/0.80)]",
            ),
            rx.el.span(
                f"Net {CrmState.kpis['net_cash']:.0f} DA",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3",
        ),
        rx.el.p(
            "Créances clients",
            class_name="text-xs font-semibold text-[rgb(var(--ap-accent-soft-rgb))] mt-5",
        ),
        rx.el.div(
            rx.foreach(
                CrmState.receivable_aging,
                lambda point: _aging_row(
                    point,
                    "h-1.5 rounded-none bg-gradient-to-r from-[rgb(var(--ap-sage-soft-rgb))] to-[rgb(var(--ap-accent-rgb))]",
                    key=f"rec-{point['bucket']}",
                ),
            ),
            class_name="flex flex-col gap-2.5 mt-2.5",
        ),
        rx.el.p(
            "Dettes fournisseurs",
            class_name="text-xs font-semibold text-[rgb(var(--ap-flame-tint-rgb))] mt-5",
        ),
        rx.el.div(
            rx.foreach(
                CrmState.payable_aging,
                lambda point: _aging_row(
                    point,
                    "h-1.5 rounded-none bg-gradient-to-r from-[rgb(var(--ap-warm-400-rgb))] to-[rgb(var(--ap-warm-250-rgb))]",
                    key=f"pay-{point['bucket']}",
                ),
            ),
            class_name="flex flex-col gap-2.5 mt-2.5",
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full xl:w-[26rem] shrink-0 pt-6",
    )


def crm_charts() -> rx.Component:
    return rx.el.section(
        crm_flow_chart(),
        crm_aging_panel(),
        class_name="flex flex-col xl:flex-row gap-4 w-full",
    )

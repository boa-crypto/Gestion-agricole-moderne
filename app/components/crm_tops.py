import reflex as rx

from app.states.crm_state import CrmState, PartnerRank


def _rank_row(
    item: PartnerRank, bar: str, amount_class: str, key: str = ""
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["name"],
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
                ),
                rx.el.p(
                    f"{item['code']} · {item['kind_label']} · {item['deals']} transaction(s)",
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.span(
                    f"{item['amount']:.0f} DA",
                    class_name=amount_class,
                ),
                rx.el.span(
                    f"{item['share']} du total",
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] text-right",
                ),
                class_name="flex flex-col shrink-0",
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.div(class_name=bar, style={"width": item["width"]}),
            class_name="h-1.5 w-full rounded-none bg-[rgb(var(--ap-surface-high-rgb))] mt-2.5",
        ),
        rx.el.div(
            rx.el.span(
                f"Score {item['score']}/100",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
            ),
            rx.el.span(
                f"Encours {item['outstanding']:.0f} DA",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-flame-tint-rgb)/0.80)] w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-2.5",
        ),
        key=key,
        class_name="w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3.5",
    )


def _empty(message: str) -> rx.Component:
    return rx.el.p(
        message,
        class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-5",
    )


def crm_tops() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.icon("crown", class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
                rx.el.span(
                    "Top 10 clients",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.span(
                    f"{CrmState.kpis['turnover']:.0f} DA de CA suivi",
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit ml-auto",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.cond(
                CrmState.top_clients.length() > 0,
                rx.el.div(
                    rx.foreach(
                        CrmState.top_clients,
                        lambda item: _rank_row(
                            item,
                            "h-1.5 rounded-none bg-gradient-to-r from-[rgb(var(--ap-sage-soft-rgb))] to-[rgb(var(--ap-accent-rgb))]",
                            "text-xs font-bold text-[rgb(var(--ap-accent-soft-rgb))] text-right",
                            key=item["id"].to_string(),
                        ),
                    ),
                    class_name="flex flex-col gap-2.5 mt-5",
                ),
                _empty("Aucune vente client enregistrée pour le moment."),
            ),
            class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] flex-1 min-w-0 pt-6",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("truck", class_name="h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]"),
                rx.el.span(
                    "Top 10 fournisseurs",
                    class_name="ap-eyebrow text-[rgb(var(--ap-flame-soft-rgb)/0.80)]",
                ),
                rx.el.span(
                    f"{CrmState.kpis['purchases']:.0f} DA d'achats",
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit ml-auto",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.cond(
                CrmState.top_suppliers.length() > 0,
                rx.el.div(
                    rx.foreach(
                        CrmState.top_suppliers,
                        lambda item: _rank_row(
                            item,
                            "h-1.5 rounded-none bg-gradient-to-r from-[rgb(var(--ap-warm-400-rgb))] to-[rgb(var(--ap-warm-250-rgb))]",
                            "text-xs font-bold text-[rgb(var(--ap-flame-tint-rgb))] text-right",
                            key=item["id"].to_string(),
                        ),
                    ),
                    class_name="flex flex-col gap-2.5 mt-5",
                ),
                _empty("Aucun achat fournisseur enregistré pour le moment."),
            ),
            class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] flex-1 min-w-0 pt-6",
        ),
        class_name="flex flex-col xl:flex-row gap-4 w-full",
    )

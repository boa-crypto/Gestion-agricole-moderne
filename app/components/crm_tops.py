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
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    f"{item['code']} · {item['kind_label']} · {item['deals']} transaction(s)",
                    class_name="text-[10px] font-medium text-emerald-100/45 truncate",
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
                    class_name="text-[10px] font-medium text-emerald-100/40 text-right",
                ),
                class_name="flex flex-col shrink-0",
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.div(class_name=bar, style={"width": item["width"]}),
            class_name="h-1.5 w-full rounded-full bg-white/[0.06] mt-2.5",
        ),
        rx.el.div(
            rx.el.span(
                f"Score {item['score']}/100",
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                f"Encours {item['outstanding']:.0f} DA",
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-amber-200/80 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-2.5",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-3.5",
    )


def _empty(message: str) -> rx.Component:
    return rx.el.p(
        message,
        class_name="text-sm font-medium text-emerald-100/50 mt-5",
    )


def crm_tops() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.icon("crown", class_name="h-4 w-4 text-lime-300"),
                rx.el.span(
                    "Top 10 clients",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                rx.el.span(
                    f"{CrmState.kpis['turnover']:.0f} DA de CA suivi",
                    class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit ml-auto",
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
                            "h-1.5 rounded-full bg-gradient-to-r from-emerald-400 to-lime-300",
                            "text-xs font-bold text-lime-200 text-right",
                            key=item["id"].to_string(),
                        ),
                    ),
                    class_name="flex flex-col gap-2.5 mt-5",
                ),
                _empty("Aucune vente client enregistrée pour le moment."),
            ),
            class_name="flex-1 min-w-0 rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("truck", class_name="h-4 w-4 text-amber-300"),
                rx.el.span(
                    "Top 10 fournisseurs",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-amber-300/80",
                ),
                rx.el.span(
                    f"{CrmState.kpis['purchases']:.0f} DA d'achats",
                    class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit ml-auto",
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
                            "h-1.5 rounded-full bg-gradient-to-r from-amber-400 to-orange-200",
                            "text-xs font-bold text-amber-200 text-right",
                            key=item["id"].to_string(),
                        ),
                    ),
                    class_name="flex flex-col gap-2.5 mt-5",
                ),
                _empty("Aucun achat fournisseur enregistré pour le moment."),
            ),
            class_name="flex-1 min-w-0 rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
        ),
        class_name="flex flex-col xl:flex-row gap-4 w-full",
    )

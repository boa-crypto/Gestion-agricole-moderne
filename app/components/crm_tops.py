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
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    f"{item['code']} · {item['kind_label']} · {item['deals']} transaction(s)",
                    class_name="text-[10px] font-medium text-[#c9c5b4]/45 truncate",
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
                    class_name="text-[10px] font-medium text-[#c9c5b4]/40 text-right",
                ),
                class_name="flex flex-col shrink-0",
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.div(class_name=bar, style={"width": item["width"]}),
            class_name="h-1.5 w-full rounded-none bg-[#191c13] mt-2.5",
        ),
        rx.el.div(
            rx.el.span(
                f"Score {item['score']}/100",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                f"Encours {item['outstanding']:.0f} DA",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#ffb894]/80 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-2.5",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3.5",
    )


def _empty(message: str) -> rx.Component:
    return rx.el.p(
        message,
        class_name="text-sm font-medium text-[#c9c5b4]/50 mt-5",
    )


def crm_tops() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.icon("crown", class_name="h-4 w-4 text-[#d8fa5e]"),
                rx.el.span(
                    "Top 10 clients",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.span(
                    f"{CrmState.kpis['turnover']:.0f} DA de CA suivi",
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit ml-auto",
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
                            "h-1.5 rounded-none bg-gradient-to-r from-[#8fb37a] to-[#d8fa5e]",
                            "text-xs font-bold text-[#e4ff9b] text-right",
                            key=item["id"].to_string(),
                        ),
                    ),
                    class_name="flex flex-col gap-2.5 mt-5",
                ),
                _empty("Aucune vente client enregistrée pour le moment."),
            ),
            class_name="flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("truck", class_name="h-4 w-4 text-[#ff8a5b]"),
                rx.el.span(
                    "Top 10 fournisseurs",
                    class_name="ap-eyebrow text-[#ff8a5b]/80",
                ),
                rx.el.span(
                    f"{CrmState.kpis['purchases']:.0f} DA d'achats",
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit ml-auto",
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
                            "h-1.5 rounded-none bg-gradient-to-r from-[#ff6a38] to-[#ffc9a8]",
                            "text-xs font-bold text-[#ffb894] text-right",
                            key=item["id"].to_string(),
                        ),
                    ),
                    class_name="flex flex-col gap-2.5 mt-5",
                ),
                _empty("Aucun achat fournisseur enregistré pour le moment."),
            ),
            class_name="flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
        ),
        class_name="flex flex-col xl:flex-row gap-4 w-full",
    )

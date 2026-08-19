import reflex as rx

from app.states.crm_state import CrmState, PartnerHit


def _chip(icon: str, label: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-3 w-3 text-lime-300"),
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold text-emerald-100/60 truncate",
        ),
        class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 w-fit max-w-full min-w-0",
    )


def _partner_card(item: PartnerHit) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["name"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    f"{item['code']} · {item['kind_label']}",
                    class_name="text-[10px] font-medium text-emerald-100/45 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                item["status_label"],
                class_name="rounded-full border border-lime-300/25 bg-lime-300/10 px-2.5 py-0.5 text-[10px] font-semibold text-lime-200 w-fit shrink-0",
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.el.div(
            _chip("map-pin", item["city"]),
            _chip("phone", item["phone"]),
            _chip("mail", item["email"]),
            _chip("gauge", f"Score {item['score']}/100"),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "CA",
                    class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
                ),
                rx.el.span(
                    f"{item['turnover']:.0f} DA",
                    class_name="text-xs font-bold text-lime-200",
                ),
                class_name="flex flex-col",
            ),
            rx.el.div(
                rx.el.span(
                    "Achats",
                    class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
                ),
                rx.el.span(
                    f"{item['purchases']:.0f} DA",
                    class_name="text-xs font-bold text-amber-200",
                ),
                class_name="flex flex-col",
            ),
            rx.el.div(
                rx.el.span(
                    "Créances",
                    class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
                ),
                rx.el.span(
                    f"{item['outstanding']:.0f} DA",
                    class_name="text-xs font-bold text-emerald-100",
                ),
                class_name="flex flex-col",
            ),
            rx.el.div(
                rx.el.span(
                    "Dettes",
                    class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
                ),
                rx.el.span(
                    f"{item['debt']:.0f} DA",
                    class_name="text-xs font-bold text-emerald-100",
                ),
                class_name="flex flex-col",
            ),
            class_name="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full mt-3 border-t border-white/10 pt-3",
        ),
        key=item["id"].to_string(),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/30 transition-colors",
    )


def crm_search() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.icon("radar", class_name="h-4 w-4 text-lime-300"),
            rx.el.span(
                "Recherche centralisée des tiers",
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
            ),
            rx.el.span(
                f"{CrmState.result_count} résultat(s)",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.div(
            rx.el.input(
                placeholder="Nom, code, wilaya, commune, téléphone, e-mail, catégorie...",
                default_value=CrmState.search,
                on_change=CrmState.set_search.debounce(400),
                class_name="flex-1 min-w-0 rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/35 focus:border-lime-300/40 focus:outline-hidden",
            ),
            rx.el.button(
                rx.icon("eraser", class_name="h-3.5 w-3.5 text-emerald-100/70"),
                rx.el.span(
                    "Réinitialiser",
                    class_name="text-xs font-semibold text-emerald-100/70",
                ),
                type="button",
                on_click=CrmState.clear_search,
                class_name="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-2.5 hover:border-lime-300/35 transition-colors w-fit",
            ),
            class_name="flex flex-col sm:flex-row gap-3 w-full mt-5",
        ),
        rx.cond(
            CrmState.result_count > 0,
            rx.el.div(
                rx.foreach(CrmState.search_results, _partner_card),
                class_name="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 w-full mt-4",
            ),
            rx.el.p(
                "Aucun tiers ne correspond à cette recherche.",
                class_name="text-sm font-medium text-emerald-100/50 mt-4",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )

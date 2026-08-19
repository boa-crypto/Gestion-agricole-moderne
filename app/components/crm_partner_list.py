import reflex as rx

from app.states.crm_partners_state import CrmPartnersState, PartnerRow


def _select(
    label: str,
    value: rx.Var,
    options: rx.Var,
    placeholder: str,
    on_change: rx.event.EventType,
) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
        ),
        rx.el.div(
            rx.el.select(
                rx.el.option(placeholder, value=""),
                rx.foreach(
                    options,
                    lambda item: rx.el.option(
                        item.replace("_", " ").lower(), value=item
                    ),
                ),
                value=value,
                on_change=on_change,
                class_name="w-full appearance-none rounded-2xl border border-white/10 bg-white/[0.05] px-3 py-2 pr-9 text-xs font-semibold capitalize text-emerald-50 focus:border-lime-300/40 focus:outline-hidden",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-emerald-100/50",
            ),
            class_name="relative w-full mt-1.5",
        ),
        class_name="flex flex-col w-full min-w-0",
    )


def crm_partner_filters() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("list-filter", class_name="h-4 w-4 text-lime-300"),
                rx.el.span(
                    CrmPartnersState.space_title,
                    class_name="text-sm font-semibold text-emerald-50",
                ),
                rx.el.span(
                    f"{CrmPartnersState.partner_count} tiers",
                    class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
                ),
                class_name="flex items-center gap-2 min-w-0",
            ),
            rx.el.button(
                rx.icon("user-round-plus", class_name="h-3.5 w-3.5"),
                rx.el.span("Nouveau tiers", class_name="text-xs font-semibold"),
                type="button",
                on_click=CrmPartnersState.open_create,
                class_name="flex items-center gap-2 rounded-full bg-lime-300 px-3.5 py-1.5 text-[#04140d] hover:bg-lime-200 transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-center justify-between gap-3 w-full",
        ),
        rx.el.input(
            placeholder="Rechercher un tiers, un code, une wilaya, un téléphone...",
            default_value=CrmPartnersState.search,
            on_change=CrmPartnersState.set_search.debounce(400),
            class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/35 focus:border-lime-300/40 focus:outline-hidden mt-4",
        ),
        rx.el.div(
            _select(
                "Type",
                CrmPartnersState.kind_filter,
                CrmPartnersState.kind_options,
                "Tous les types",
                CrmPartnersState.set_kind_filter,
            ),
            _select(
                "Statut",
                CrmPartnersState.status_filter,
                CrmPartnersState.status_options,
                "Tous les statuts",
                CrmPartnersState.set_status_filter,
            ),
            class_name="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full mt-3",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon(
                    "archive",
                    class_name=rx.cond(
                        CrmPartnersState.include_archived,
                        "h-3.5 w-3.5 text-[#04140d]",
                        "h-3.5 w-3.5 text-emerald-100/60",
                    ),
                ),
                rx.el.span(
                    "Inclure les archivés",
                    class_name=rx.cond(
                        CrmPartnersState.include_archived,
                        "text-[11px] font-semibold text-[#04140d]",
                        "text-[11px] font-semibold text-emerald-100/60",
                    ),
                ),
                type="button",
                on_click=CrmPartnersState.toggle_archived,
                class_name=rx.cond(
                    CrmPartnersState.include_archived,
                    "flex items-center gap-2 rounded-full bg-lime-300 px-3 py-1.5 transition-colors w-fit",
                    "flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 hover:border-lime-300/35 transition-colors w-fit",
                ),
            ),
            rx.el.button(
                rx.icon("eraser", class_name="h-3.5 w-3.5 text-emerald-100/60"),
                rx.el.span(
                    "Réinitialiser",
                    class_name="text-[11px] font-semibold text-emerald-100/60",
                ),
                type="button",
                on_click=CrmPartnersState.clear_filters,
                class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 hover:border-lime-300/35 transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-3",
        ),
        class_name="w-full",
    )


def _stat(label: str, value: rx.Var | str, tone: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
        ),
        rx.el.span(value, class_name=tone),
        class_name="flex flex-col min-w-0",
    )


def _partner_card(item: PartnerRow) -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["name"],
                    class_name="text-sm font-semibold text-emerald-50 truncate text-left",
                ),
                rx.el.p(
                    f"{item['code']} · {item['kind_label']}",
                    class_name="text-[10px] font-medium text-emerald-100/45 truncate text-left",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                item["status_label"],
                class_name=rx.cond(
                    item["is_archived"],
                    "rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-100/50 w-fit shrink-0",
                    "rounded-full border border-lime-300/25 bg-lime-300/10 px-2.5 py-0.5 text-[10px] font-semibold text-lime-200 w-fit shrink-0",
                ),
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.span(
                item["city"],
                class_name="text-[10px] font-medium text-emerald-100/45 truncate",
            ),
            rx.el.span(
                f"Score {item['score']}/100",
                class_name="text-[10px] font-semibold text-lime-200/80 ml-auto shrink-0",
            ),
            class_name="flex items-center gap-2 w-full min-w-0 mt-2",
        ),
        rx.el.div(
            _stat(
                "CA",
                f"{item['turnover']:.0f} DA",
                "text-[11px] font-bold text-lime-200 truncate",
            ),
            _stat(
                "Achats",
                f"{item['purchases']:.0f} DA",
                "text-[11px] font-bold text-amber-200 truncate",
            ),
            _stat(
                "Créances",
                f"{item['receivable']:.0f} DA",
                "text-[11px] font-bold text-emerald-100 truncate",
            ),
            _stat(
                "Opérations",
                f"{item['deals']}",
                "text-[11px] font-bold text-emerald-100 truncate",
            ),
            class_name="grid grid-cols-2 gap-2 w-full mt-3 border-t border-white/10 pt-3",
        ),
        type="button",
        on_click=CrmPartnersState.select_partner(item["id"]),
        key=item["id"].to_string(),
        class_name=rx.cond(
            CrmPartnersState.selected_id == item["id"],
            "w-full rounded-2xl border border-lime-300/45 bg-lime-300/[0.08] p-3.5 text-left transition-colors",
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-3.5 text-left hover:border-lime-300/30 hover:bg-white/[0.06] transition-colors",
        ),
    )


def crm_partner_list() -> rx.Component:
    return rx.el.section(
        crm_partner_filters(),
        rx.cond(
            CrmPartnersState.partner_count > 0,
            rx.el.div(
                rx.foreach(CrmPartnersState.partners, _partner_card),
                class_name="flex flex-col gap-2.5 w-full mt-4 max-h-[46rem] overflow-y-auto pr-1",
            ),
            rx.el.p(
                "Aucun tiers ne correspond à ces filtres. Créez un nouveau tiers ou élargissez la recherche.",
                class_name="text-sm font-medium text-emerald-100/50 mt-5",
            ),
        ),
        class_name="w-full xl:w-[27rem] shrink-0 rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl",
    )

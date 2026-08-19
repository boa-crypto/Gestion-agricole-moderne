import reflex as rx

from app.components.guide_help import help_button
from app.states.crm_state import CrmState, Tab


def _pill(icon: str, label: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300"),
        rx.el.span(label, class_name="text-xs font-medium text-emerald-50/80"),
        class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur-xl w-fit",
    )


def _tab(item: Tab) -> rx.Component:
    return rx.el.button(
        rx.icon(
            item["icon"],
            class_name=rx.cond(
                CrmState.active_tab == item["key"],
                "h-3.5 w-3.5 stroke-[#04140d]",
                "h-3.5 w-3.5 stroke-emerald-100/60",
            ),
        ),
        rx.el.span(
            item["label"],
            class_name=rx.cond(
                CrmState.active_tab == item["key"],
                "text-xs font-semibold text-[#04140d]",
                "text-xs font-semibold text-emerald-100/70",
            ),
        ),
        type="button",
        on_click=CrmState.set_tab(item["key"]),
        class_name=rx.cond(
            CrmState.active_tab == item["key"],
            "flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 transition-colors w-fit",
            "flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 hover:border-lime-300/35 hover:bg-white/[0.08] transition-colors w-fit",
        ),
    )


def crm_tabs() -> rx.Component:
    return rx.el.nav(
        rx.foreach(CrmState.tabs, lambda item: _tab(item)),
        aria_label="Navigation CRM",
        class_name="flex flex-wrap items-center gap-2 w-full",
    )


def crm_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("handshake", class_name="h-4 w-4 text-lime-300"),
                    rx.el.span(
                        "Cockpit commercial",
                        class_name="text-[11px] font-semibold uppercase tracking-[0.32em] text-lime-300/90",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "CRM & Partenaires",
                    class_name="font-['Instrument_Serif'] text-4xl md:text-5xl leading-[1.05] text-emerald-50 mt-3",
                ),
                rx.el.p(
                    "Vision consolidée des clients, fournisseurs et partenaires : "
                    "chiffre d'affaires, achats, créances, dettes, échéances et "
                    "risques financiers de l'exploitation.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-3 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _pill("calendar-days", CrmState.today_label),
                _pill("sprout", CrmState.season_label),
                _pill(
                    "bell-ring",
                    f"{CrmState.alert_count} alerte(s) financière(s)",
                ),
                help_button("crm", "Guide CRM"),
                rx.el.button(
                    rx.cond(
                        CrmState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#04140d]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#04140d]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#04140d]"),
                    on_click=CrmState.load_crm,
                    class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        rx.el.div(crm_tabs(), class_name="w-full mt-6"),
        class_name="w-full border-b border-white/10 pb-8 mt-6",
    )

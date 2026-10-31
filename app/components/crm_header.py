import reflex as rx

from app.components.guide_help import help_button
from app.states.crm_state import CrmState, Tab
from app.states.menu_auth_state import MenuAuthState


def _pill(icon: str, label: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-3.5 w-3.5 text-[#d8fa5e]"),
        rx.el.span(label, class_name="text-xs font-medium text-[#f2efe4]/80"),
        class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
    )


def _tab(item: Tab) -> rx.Component:
    return rx.el.button(
        rx.icon(
            item["icon"],
            class_name=rx.cond(
                CrmState.active_tab == item["key"],
                "h-3.5 w-3.5 stroke-[#0A0A08]",
                "h-3.5 w-3.5 stroke-[#c9c5b4]/60",
            ),
        ),
        rx.el.span(
            item["label"],
            class_name=rx.cond(
                CrmState.active_tab == item["key"],
                "text-xs font-semibold text-[#0A0A08]",
                "text-xs font-semibold text-[#c9c5b4]/70",
            ),
        ),
        type="button",
        on_click=CrmState.set_tab(item["key"]),
        class_name=rx.cond(
            CrmState.active_tab == item["key"],
            "flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2 transition-colors w-fit",
            "flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2 hover:border-[#d8fa5e]/35 hover:bg-[#1e2216] transition-colors w-fit",
        ),
    )


def crm_tabs() -> rx.Component:
    return rx.el.nav(
        rx.foreach(
            CrmState.tabs,
            lambda item: rx.cond(
                MenuAuthState.allowed_crm_tabs.contains(item["key"]),
                _tab(item),
                rx.fragment(),
            ),
        ),
        aria_label="Navigation CRM",
        class_name="flex flex-wrap items-center gap-2 w-full",
    )


def crm_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("handshake", class_name="h-4 w-4 text-[#d8fa5e]"),
                    rx.el.span(
                        "Cockpit commercial",
                        class_name="ap-eyebrow text-[#D8FA5E]",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "CRM & Partenaires",
                    class_name="ap-display text-[clamp(2.4rem,4.6vw,4.1rem)] text-[#f2efe4] mt-3",
                ),
                rx.el.p(
                    "Vision consolidée des clients, fournisseurs et partenaires : "
                    "chiffre d'affaires, achats, créances, dettes, échéances et "
                    "risques financiers de l'exploitation.",
                    class_name="mt-4 text-[13px] leading-relaxed text-[#C9C5B4]/70 max-w-2xl",
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
                            class_name="h-4 w-4 animate-spin text-[#0A0A08]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#0A0A08]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#0A0A08]"),
                    on_click=CrmState.load_crm,
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B]",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        rx.el.div(crm_tabs(), class_name="w-full mt-6"),
        class_name="w-full border-b border-[#F2EFE4]/12 pb-8",
    )

"""En-tête éditorial du cockpit commercial (CRM & partenaires)."""

from __future__ import annotations

import reflex as rx

from app.components.design import (
    index_rail,
    index_tab,
    meta_ledger,
    meta_row,
    page_hero,
)
from app.components.guide_help import help_button
from app.states.crm_state import CrmState, Tab
from app.states.menu_auth_state import MenuAuthState


def _tab(item: Tab) -> rx.Component:
    return index_tab(
        item["label"],
        active=CrmState.active_tab == item["key"],
        on_click=CrmState.set_tab(item["key"]),
        icon=item["icon"],
    )


def crm_tabs() -> rx.Component:
    return index_rail(
        rx.foreach(
            CrmState.tabs,
            lambda item: rx.cond(
                MenuAuthState.allowed_crm_tabs.contains(item["key"]),
                _tab(item),
                rx.fragment(),
            ),
        ),
        label="Navigation CRM",
        class_name="mt-8",
    )


def _refresh() -> rx.Component:
    return rx.el.button(
        rx.cond(
            CrmState.is_loading,
            rx.icon("loader-circle", class_name="h-3.5 w-3.5 animate-spin"),
            rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
        ),
        rx.el.span("Actualiser"),
        type="button",
        on_click=CrmState.load_crm,
        disabled=CrmState.is_loading,
        class_name=(
            "ap-mono inline-flex w-fit items-center justify-center gap-2 border "
            "border-[#D8FA5E] bg-[#D8FA5E] px-3.5 py-2.5 text-[10px] uppercase "
            "tracking-[0.18em] text-[#0A0A08] transition-colors "
            "hover:border-[#E4FF9B] hover:bg-[#E4FF9B] "
            "disabled:cursor-not-allowed disabled:opacity-45"
        ),
    )


def crm_header() -> rx.Component:
    return rx.el.div(
        page_hero(
            "Cockpit commercial",
            "CRM & Partenaires",
            "Vision consolidée des clients, fournisseurs et partenaires : chiffre "
            "d'affaires, achats, créances, dettes, échéances et risques financiers "
            "de l'exploitation.",
            meta=meta_ledger(
                meta_row("Jour", CrmState.today_label),
                meta_row("Campagne", CrmState.season_label),
                meta_row(
                    "Alertes financières",
                    CrmState.alert_count.to_string(),
                    tone="flame",
                ),
            ),
            actions=rx.el.div(
                help_button("crm", "Guide CRM"),
                _refresh(),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="pb-8",
        ),
        crm_tabs(),
        class_name="w-full",
    )

"""Rapports phénologiques multi-parcelles et multi-cultures."""

import reflex as rx

from app.components.design import meta_ledger, meta_row, page_hero, refresh_button
from app.components.phenology_ops_panels import (
    phenology_alerts_panel,
    phenology_filters,
    phenology_kpis,
    phenology_operations_panel,
    phenology_planned_panel,
    phenology_stage_board,
)
from app.components.shell import app_shell
from app.states.phenology_ops_state import PhenologyOpsState


def _space_header() -> rx.Component:
    return page_hero(
        "Rapports agronomiques",
        "État phénologique de l'exploitation",
        "Stade actuel et prochain stade de chaque culture, opérations généralement associées, anomalies à vérifier et comparaison prévu / réel lorsque les données existent.",
        meta=meta_ledger(
            meta_row("Jour", PhenologyOpsState.today_label),
        ),
        actions=rx.el.div(
            refresh_button(
                on_click=PhenologyOpsState.load_operational,
                loading=PhenologyOpsState.is_loading,
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
    )


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="animate-pulse h-28 rounded-none bg-[#16190f]"),
        rx.el.div(class_name="animate-pulse h-64 rounded-none bg-[#16190f]"),
        rx.el.div(class_name="animate-pulse h-64 rounded-none bg-[#16190f]"),
        class_name="flex flex-col gap-4 w-full",
    )


def reports_page() -> rx.Component:
    return app_shell(
        rx.el.div(
            _space_header(),
            rx.el.div(
                rx.cond(
                    PhenologyOpsState.is_loading,
                    _skeleton(),
                    rx.el.div(
                        phenology_kpis(),
                        phenology_filters(),
                        phenology_stage_board(),
                        phenology_alerts_panel(),
                        phenology_operations_panel(),
                        phenology_planned_panel(),
                        class_name="flex flex-col gap-4 w-full",
                    ),
                ),
                class_name="w-full mt-8",
            ),
            class_name="flex w-full flex-col gap-6",
        ),
        "rapports",
    )

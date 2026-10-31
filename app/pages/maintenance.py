import reflex as rx

from app.components.design import meta_ledger, meta_row, page_hero, refresh_button
from app.components.equipment_detail import equipment_detail
from app.components.equipment_list import equipment_list
from app.components.fleet_board import deadline_planner, fleet_health_map
from app.components.fleet_filters import fleet_filters
from app.components.fleet_kpis import fleet_kpis
from app.components.guide_help import help_button
from app.components.maintenance_forms import maintenance_modals
from app.components.maintenance_journal import maintenance_journal
from app.components.shell import app_shell
from app.states.maintenance_state import MaintenanceState


def _space_header() -> rx.Component:
    return page_hero(
        "Atelier & flotte agricole",
        "Engins & maintenance",
        "Planning des échéances machine, santé de la flotte, opérations préventives et correctives, coûts et affectation des responsables.",
        meta=meta_ledger(
            meta_row("Jour", MaintenanceState.today_label),
            meta_row("Opérations en retard", f"{MaintenanceState.kpis['overdue_ops']:.0f}", tone="flame"),
        ),
        actions=rx.el.div(
            help_button("maintenance", "Guide atelier"),
            refresh_button(
                on_click=MaintenanceState.load_fleet,
                loading=MaintenanceState.is_loading,
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
    )


def maintenance_page() -> rx.Component:
    return app_shell(
        rx.el.div(
            _space_header(),
            rx.el.div(
                fleet_kpis(),
                fleet_filters(),
                rx.el.div(
                    rx.el.div(
                        deadline_planner(),
                        id="nav-echeances",
                        class_name="flex-1 min-w-0 scroll-mt-6",
                    ),
                    fleet_health_map(),
                    class_name="flex flex-col xl:flex-row gap-4 w-full",
                ),
                maintenance_journal(),
                rx.el.div(
                    equipment_list(),
                    equipment_detail(),
                    class_name="flex flex-col xl:flex-row gap-4 w-full",
                ),
                class_name="flex flex-col gap-4 w-full mt-8",
            ),
            maintenance_modals(),
            class_name="flex w-full flex-col gap-6",
        ),
        "maintenance",
    )

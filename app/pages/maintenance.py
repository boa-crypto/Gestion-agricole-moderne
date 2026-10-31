import reflex as rx

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
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("wrench", class_name="h-4 w-4 text-[#d8fa5e]"),
                    rx.el.span(
                        "Atelier & flotte agricole",
                        class_name="ap-eyebrow text-[#D8FA5E]",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Engins & maintenance",
                    class_name="ap-display text-[clamp(2.4rem,4.6vw,4.1rem)] text-[#f2efe4] mt-3",
                ),
                rx.el.p(
                    "Planning des échéances machine, santé de la flotte, opérations préventives et correctives, coûts et affectation des responsables.",
                    class_name="mt-4 text-[13px] leading-relaxed text-[#C9C5B4]/70 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "calendar-days", class_name="h-3.5 w-3.5 text-[#d8fa5e]"
                    ),
                    rx.el.span(
                        MaintenanceState.today_label,
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                rx.el.div(
                    rx.icon(
                        "triangle-alert",
                        class_name="h-3.5 w-3.5 text-[#ff8a5b]",
                    ),
                    rx.el.span(
                        f"{MaintenanceState.kpis['overdue_ops']:.0f} opération(s) en retard",
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                help_button("maintenance", "Guide atelier"),
                rx.el.button(
                    rx.cond(
                        MaintenanceState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#0A0A08]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#0A0A08]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#0A0A08]"),
                    on_click=MaintenanceState.load_fleet,
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B]",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-[#F2EFE4]/12 pb-8",
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

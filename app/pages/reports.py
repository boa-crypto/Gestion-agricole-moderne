"""Rapports phénologiques multi-parcelles et multi-cultures."""

import reflex as rx

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
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("bar-chart-3", class_name="h-4 w-4 text-[#d8fa5e]"),
                    rx.el.span(
                        "Rapports agronomiques",
                        class_name="ap-eyebrow text-[#D8FA5E]",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "État phénologique de l'exploitation",
                    class_name="ap-display text-[clamp(2.4rem,4.6vw,4.1rem)] text-[#f2efe4] mt-3",
                ),
                rx.el.p(
                    "Stade actuel et prochain stade de chaque culture, opérations généralement associées, anomalies à vérifier et comparaison prévu / réel lorsque les données existent.",
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
                        PhenologyOpsState.today_label,
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                rx.el.button(
                    rx.cond(
                        PhenologyOpsState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#0A0A08]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#0A0A08]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#0A0A08]"),
                    on_click=PhenologyOpsState.load_operational,
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B]",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-[#F2EFE4]/12 pb-8",
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

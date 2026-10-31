import reflex as rx

from app.components.contour_control import (
    contour_control_board,
    contour_history_panel,
)
from app.components.guide_help import help_button
from app.components.map_canvas import map_canvas
from app.components.map_parcel_detail import map_parcel_detail
from app.components.map_sidebar import map_sidebar
from app.components.phenology_ops_panels import (
    phenology_alerts_panel,
    phenology_kpis,
    phenology_stage_board,
)
from app.components.remediation_panels import contour_validation_panel
from app.components.shell import app_shell
from app.states.cartography_state import CartographyState


def _space_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("map-pinned", class_name="h-4 w-4 text-[#d8fa5e]"),
                    rx.el.span(
                        "Géomatique agricole",
                        class_name="ap-eyebrow text-[#D8FA5E]",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Cartographie interactive",
                    class_name="ap-display text-[clamp(2.4rem,4.6vw,4.1rem)] text-[#f2efe4] mt-3",
                ),
                rx.el.p(
                    "Contours réels des îlots sur fond cartographique, sélection au clic, fiche parcellaire complète, métadonnées de géométrie et historique intégral des interventions.",
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
                        CartographyState.today_label,
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                rx.el.div(
                    rx.icon(
                        "pen-tool", class_name="h-3.5 w-3.5 text-[#ff8a5b]"
                    ),
                    rx.el.span(
                        f"{CartographyState.mapped_count} contour(s) enregistré(s)",
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                help_button("cartographie", "Guide géomatique"),
                rx.el.button(
                    rx.cond(
                        CartographyState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#0A0A08]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#0A0A08]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#0A0A08]"),
                    on_click=CartographyState.load_map,
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B]",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-[#F2EFE4]/12 pb-8",
    )


def cartography_page() -> rx.Component:
    return app_shell(
        rx.el.div(
            _space_header(),
            rx.el.div(
                rx.el.div(
                    map_sidebar(),
                    map_canvas(),
                    class_name="flex flex-col xl:flex-row gap-4 w-full",
                ),
                map_parcel_detail(),
                phenology_kpis(),
                phenology_stage_board(),
                phenology_alerts_panel(),
                contour_control_board(),
                contour_history_panel(),
                contour_validation_panel(),
                class_name="flex flex-col gap-4 w-full mt-8",
            ),
            class_name="flex w-full flex-col gap-6",
        ),
        "cartographie",
    )

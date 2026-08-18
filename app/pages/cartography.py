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
from app.components.side_rail import side_rail
from app.states.cartography_state import CartographyState


def _space_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("map-pinned", class_name="h-4 w-4 text-lime-300"),
                    rx.el.span(
                        "Géomatique agricole",
                        class_name="text-[11px] font-semibold uppercase tracking-[0.32em] text-lime-300/90",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Cartographie interactive",
                    class_name="font-['Instrument_Serif'] text-4xl md:text-5xl leading-[1.05] text-emerald-50 mt-3",
                ),
                rx.el.p(
                    "Contours réels des îlots sur fond cartographique, sélection au clic, fiche parcellaire complète, métadonnées de géométrie et historique intégral des interventions.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-3 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "calendar-days", class_name="h-3.5 w-3.5 text-lime-300"
                    ),
                    rx.el.span(
                        CartographyState.today_label,
                        class_name="text-xs font-medium text-emerald-50/80",
                    ),
                    class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur-xl w-fit",
                ),
                rx.el.div(
                    rx.icon(
                        "pen-tool", class_name="h-3.5 w-3.5 text-amber-300"
                    ),
                    rx.el.span(
                        f"{CartographyState.mapped_count} contour(s) enregistré(s)",
                        class_name="text-xs font-medium text-emerald-50/80",
                    ),
                    class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur-xl w-fit",
                ),
                help_button("cartographie", "Guide géomatique"),
                rx.el.button(
                    rx.cond(
                        CartographyState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#04140d]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#04140d]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#04140d]"),
                    on_click=CartographyState.load_map,
                    class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-white/10 pb-8 mt-6",
    )


def cartography_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            class_name="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-[#04120c]/35 via-[#04120c]/45 to-[#020a07]/60",
        ),
        rx.el.div(
            side_rail("cartographie"),
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
            class_name="relative z-10 w-full max-w-[110rem] mx-auto px-4 sm:px-8 md:pl-24 lg:pl-28 py-10 pb-28 md:pb-10",
        ),
        class_name="relative min-h-screen w-full font-['Inter'] bg-[#04120c] bg-[url('/wide_cinematic_background.png')] bg-cover bg-center bg-fixed text-emerald-50 antialiased",
    )

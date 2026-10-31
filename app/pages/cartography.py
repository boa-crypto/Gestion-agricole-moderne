import reflex as rx

from app.components.contour_control import (
    contour_control_board,
    contour_history_panel,
)
from app.components.design import meta_ledger, meta_row, page_hero, refresh_button
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
    return page_hero(
        "Géomatique agricole",
        "Cartographie interactive",
        "Contours réels des îlots sur fond cartographique, sélection au clic, fiche parcellaire complète, métadonnées de géométrie et historique intégral des interventions.",
        meta=meta_ledger(
            meta_row("Jour", CartographyState.today_label),
            meta_row("Contours", CartographyState.mapped_count),
        ),
        actions=rx.el.div(
            help_button("cartographie", "Guide géomatique"),
            refresh_button(
                on_click=CartographyState.load_map,
                loading=CartographyState.is_loading,
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
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

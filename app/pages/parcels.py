import reflex as rx

from app.components.guide_help import help_button
from app.components.parcel_detail import parcel_detail
from app.components.parcel_filters import parcel_filters
from app.components.parcel_forms import parcel_modals
from app.components.parcel_list import parcel_list
from app.components.phenology_panel import phenology_panel
from app.components.catalog_bridge import (
    catalog_context_panel,
    catalog_shortcut,
)
from app.components.shell import app_shell
from app.states.parcels_state import ParcelsState


def _space_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("map", class_name="h-4 w-4 text-[#d8fa5e]"),
                    rx.el.span(
                        "Parcellaire & itinéraires",
                        class_name="ap-eyebrow text-[#D8FA5E]",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Parcelles & cultures",
                    class_name="ap-display text-[clamp(2.4rem,4.6vw,4.1rem)] text-[#f2efe4] mt-3",
                ),
                rx.el.p(
                    "Créez, filtrez et pilotez chaque îlot : fiches parcellaires, fiches culturales et suivi des stades phénologiques.",
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
                        ParcelsState.today_label,
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                help_button("parcelles", "Guide parcellaire"),
                rx.el.button(
                    rx.cond(
                        ParcelsState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#0A0A08]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#0A0A08]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#0A0A08]"),
                    on_click=ParcelsState.load_space,
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B]",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-[#F2EFE4]/12 pb-8",
    )


def parcels_page() -> rx.Component:
    return app_shell(
        rx.el.div(
            catalog_shortcut("parcelles"),
            _space_header(),
            rx.el.div(
                parcel_filters(),
                rx.el.div(
                    parcel_list(),
                    parcel_detail(),
                    class_name="flex flex-col xl:flex-row gap-4 w-full",
                ),
                phenology_panel(),
                class_name="flex flex-col gap-4 w-full mt-8",
            ),
            catalog_context_panel(),
            parcel_modals(),
            class_name="flex w-full flex-col gap-6",
        ),
        "parcelles",
    )

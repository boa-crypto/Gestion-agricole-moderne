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
from app.components.side_rail import side_rail
from app.states.parcels_state import ParcelsState


def _space_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("map", class_name="h-4 w-4 text-lime-300"),
                    rx.el.span(
                        "Parcellaire & itinéraires",
                        class_name="text-[11px] font-semibold uppercase tracking-[0.32em] text-lime-300/90",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Parcelles & cultures",
                    class_name="font-['Instrument_Serif'] text-4xl md:text-5xl leading-[1.05] text-emerald-50 mt-3",
                ),
                rx.el.p(
                    "Créez, filtrez et pilotez chaque îlot : fiches parcellaires, fiches culturales et suivi des stades phénologiques.",
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
                        ParcelsState.today_label,
                        class_name="text-xs font-medium text-emerald-50/80",
                    ),
                    class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur-xl w-fit",
                ),
                help_button("parcelles", "Guide parcellaire"),
                rx.el.button(
                    rx.cond(
                        ParcelsState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#04140d]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#04140d]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#04140d]"),
                    on_click=ParcelsState.load_space,
                    class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-white/10 pb-8 mt-6",
    )


def parcels_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            class_name="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-[#04120c]/35 via-[#04120c]/45 to-[#020a07]/60",
        ),
        rx.el.div(
            side_rail("parcelles"),
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
            class_name="relative z-10 w-full max-w-[110rem] mx-auto px-4 sm:px-8 md:pl-24 lg:pl-28 py-10 pb-28 md:pb-10",
        ),
        class_name="relative min-h-screen w-full font-['Inter'] bg-[#04120c] bg-[url('/wide_cinematic_background.png')] bg-cover bg-center bg-fixed text-emerald-50 antialiased",
    )

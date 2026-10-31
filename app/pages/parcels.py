import reflex as rx

from app.components.design import meta_ledger, meta_row, page_hero
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


def _refresh() -> rx.Component:
    return rx.el.button(
        rx.cond(
            ParcelsState.is_loading,
            rx.icon("loader-circle", class_name="h-3.5 w-3.5 animate-spin"),
            rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
        ),
        rx.el.span("Actualiser"),
        type="button",
        on_click=ParcelsState.load_space,
        disabled=ParcelsState.is_loading,
        class_name=(
            "ap-mono inline-flex w-fit items-center justify-center gap-2 border "
            "border-[#D8FA5E] bg-[#D8FA5E] px-3.5 py-2.5 text-[10px] uppercase "
            "tracking-[0.18em] text-[#0A0A08] transition-colors "
            "hover:border-[#E4FF9B] hover:bg-[#E4FF9B] "
            "disabled:cursor-not-allowed disabled:opacity-45"
        ),
    )


def _space_header() -> rx.Component:
    return page_hero(
        "Parcellaire & itinéraires",
        "Parcelles & cultures",
        "Créez, filtrez et pilotez chaque îlot : fiches parcellaires, fiches "
        "culturales et suivi des stades phénologiques.",
        meta=meta_ledger(meta_row("Jour", ParcelsState.today_label)),
        actions=rx.el.div(
            help_button("parcelles", "Guide parcellaire"),
            _refresh(),
            class_name="flex flex-wrap items-center gap-2",
        ),
        class_name="pb-8",
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

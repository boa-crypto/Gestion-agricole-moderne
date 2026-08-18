"""Page de consultation et de pilotage du référentiel cultures."""

import reflex as rx

from app.components.catalog_dates import catalog_dates
from app.components.catalog_detail import catalog_detail
from app.components.catalog_filters import catalog_filters
from app.components.catalog_hero import (
    catalog_coverage,
    catalog_header,
    catalog_radar,
)
from app.components.catalog_list import catalog_list
from app.components.side_rail import side_rail


def catalog_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            class_name="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-[#04120c]/35 via-[#04120c]/45 to-[#020a07]/60",
        ),
        rx.el.div(
            side_rail("referentiel"),
            catalog_header(),
            rx.el.div(
                catalog_coverage(),
                catalog_radar(),
                catalog_filters(),
                rx.el.div(
                    catalog_list(),
                    catalog_detail(),
                    class_name="flex flex-col xl:flex-row gap-4 w-full items-start",
                ),
                catalog_dates(),
                class_name="flex flex-col gap-4 w-full mt-8",
            ),
            class_name="relative z-10 w-full max-w-[110rem] mx-auto px-4 sm:px-8 md:pl-24 lg:pl-28 py-10 pb-28 md:pb-10",
        ),
        class_name="relative min-h-screen w-full font-['Inter'] bg-[#04120c] bg-[url('/wide_cinematic_background.png')] bg-cover bg-center bg-fixed text-emerald-50 antialiased",
    )

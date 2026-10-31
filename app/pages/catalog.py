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
from app.components.shell import app_shell


def catalog_page() -> rx.Component:
    return app_shell(
        rx.el.div(
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
            class_name="flex w-full flex-col gap-6",
        ),
        "referentiel",
    )

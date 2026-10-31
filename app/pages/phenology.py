"""Page d'administration du référentiel phénologique AgriPro."""

import reflex as rx

from app.components.phenology_admin import phenology_admin
from app.components.shell import app_shell


def phenology_admin_page() -> rx.Component:
    return app_shell(
        rx.el.div(
            phenology_admin(),
            class_name="flex w-full flex-col gap-6",
        ),
        "phenologie",
    )
